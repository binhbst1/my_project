from django.shortcuts import render

# Create your views here.
from rest_framework.exceptions import APIException  # Import APIException here
from django.db.models import F
import datetime
from django.db import transaction
from rest_framework import viewsets
from rest_framework import mixins
from app.models import Endpoint
from app.serializers import EndpointSerializer
from app.models import MLModel
from app.serializers import MLModelSerializer
from app.models import MLModelStatus
from app.serializers import MLModelStatusSerializer
from app.models import MLRequest
from app.serializers import MLRequestSerializer
from app.models import ABTest
from app.serializers import ABTestSerializer
import json
from numpy.random import rand
from rest_framework import views, status
from rest_framework.response import Response
from server.wsgi import registry
class EndpointViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EndpointSerializer
    queryset = Endpoint.objects.all()
class MLModelViewSet( mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MLModelSerializer
    queryset = MLModel.objects.all()
def deactivate_other_statuses(instance):
    old_statuses = MLModelStatus.objects.filter(parent_mlmodel=instance.parent_mlmodel,created_at__lt=instance.created_at,active=True)
    for i in range(len(old_statuses)):
        old_statuses[i].active = False
    MLModelStatus.objects.bulk_update(old_statuses, ["active"])
class MLModelStatusViewSet(   mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = MLModelStatusSerializer
    queryset = MLModelStatus.objects.all()
    # gọi bởi CreateModelMixin class để lưu một object mới
    def perform_create(self, serializer):
        try:
            # quản lý các tiến trình nhỏ trong Django transaction. Success thì active == True và ngược lại
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)
        except Exception as e:
            raise APIException(str(e))

class MLRequestViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.UpdateModelMixin):
    serializer_class = MLRequestSerializer
    queryset = MLRequest.objects.all()

class PredictView(views.APIView):
    def post(self, request, endpoint_name, format=None):
        algorithm_status = self.request.query_params.get("status", "production")
        algorithm_version = self.request.query_params.get("version")
        algs = MLModel.objects.filter(parent_endpoint__name = endpoint_name, status__status = algorithm_status, status__active=True)
        if algorithm_version is not None:
            algs = algs.filter(version = algorithm_version)
        if len(algs) == 0:
            return Response(
                {"status": "Error", "message": "ML algorithm is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(algs) != 1 and algorithm_status != "ab_testing":
            return Response(
                {"status": "Error", "message": "ML algorithm selection is ambiguous. Please specify algorithm version."},
                status=status.HTTP_400_BAD_REQUEST,
            )
         
        alg_index = 0
        if algorithm_status == "ab_testing":
            alg_index = 0 if rand() < 0.5 else 1
        algorithm_object = registry.endpoints[algs[alg_index].id]
        prediction = algorithm_object.compute_prediction(request.data)
        label = prediction["label"] if "label" in prediction else "error"
        ml_request = MLRequest(
            input_data=json.dumps(request.data),
            full_response=prediction,
            response=label,
            feedback="",
            parent_mlmodel=algs[alg_index],
        )
        ml_request.save()

        prediction["request_id"] = ml_request.id

        return Response(prediction)
class ABTestViewSet(    mixins.RetrieveModelMixin,    mixins.ListModelMixin,
    viewsets.GenericViewSet,    mixins.CreateModelMixin,    mixins.UpdateModelMixin,):
    serializer_class = ABTestSerializer
    queryset = ABTest.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save()

                # Update status for the first algorithm
                status_1 = MLModelStatus(
                    status="ab_testing",
                    created_by=instance.created_by,
                    parent_mlmodel=instance.parent_mlmodel_1,
                    active=True,
                )
                status_1.save()
                deactivate_other_statuses(status_1)

                # Update status for the second algorithm
                status_2 = MLModelStatus(
                    status="ab_testing",
                    created_by=instance.created_by,
                    parent_mlmodel=instance.parent_mlmodel_2,
                    active=True,
                )
                status_2.save()
                deactivate_other_statuses(status_2)

        except Exception as e:
            raise APIException(str(e))


class StopABTestView(views.APIView):
    def post(self, request, ab_test_id, format=None):
        try:
            ab_test = ABTest.objects.get(pk=ab_test_id)
            if ab_test.ended_at is not None:
                return Response({"message": "AB Test already finished."})

            date_now = datetime.datetime.now()
            # alg #1 accuracy
            all_responses_1 = MLRequest.objects.filter(parent_mlmodel=ab_test.parent_mlmodel_1, created_at__gt = ab_test.created_at, created_at__lt = date_now).count()
            correct_responses_1 = MLRequest.objects.filter(parent_mlmodel=ab_test.parent_mlmodel_1, created_at__gt = ab_test.created_at, created_at__lt = date_now, response=F('feedback')).count()
            accuracy_1 = correct_responses_1 / float(all_responses_1)
            print(all_responses_1, correct_responses_1, accuracy_1)

            # alg #2 accuracy
            all_responses_2 = MLRequest.objects.filter(parent_mlmodel=ab_test.parent_mlmodel_2, created_at__gt = ab_test.created_at, created_at__lt = date_now).count()
            correct_responses_2 = MLRequest.objects.filter(parent_mlmodel=ab_test.parent_mlmodel_2, created_at__gt = ab_test.created_at, created_at__lt = date_now, response=F('feedback')).count()
            accuracy_2 = correct_responses_2 / float(all_responses_2)
            print(all_responses_2, correct_responses_2, accuracy_2)
            # select algorithm with higher accuracy
            alg_id_1, alg_id_2 = ab_test.parent_mlmodel_1, ab_test.parent_mlmodel_2
            # swap
            if accuracy_1 < accuracy_2:
                alg_id_1, alg_id_2 = alg_id_2, alg_id_1
            status_1 = MLModelStatus(status = "production",
                            created_by=ab_test.created_by,
                            parent_mlmodel = alg_id_1,
                            active=True)
            status_1.save()
            deactivate_other_statuses(status_1)
            # update status for second algorithm
            status_2 = MLModelStatus(status = "testing",
                            created_by=ab_test.created_by,
                            parent_mlmodel = alg_id_2, active=True)
            status_2.save()
            deactivate_other_statuses(status_2)
            summary = "Model #1 accuracy: {}, Model #2 accuracy: {}".format(accuracy_1, accuracy_2)
            ab_test.ended_at = date_now
            ab_test.summary = summary
            ab_test.save()
        except Exception as e:
            return Response({"status": "Error", "message": str(e)},
                            status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"message": "AB Test finished.", "summary": summary})


