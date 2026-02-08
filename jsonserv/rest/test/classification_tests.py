from django.utils.http import urlencode
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Тестируемые модели
from jsonserv.core.models import Classification
# from jsonserv.toolover.models import ToolClass

from jsonserv.rest import views


class ClassificationTests(APITestCase):
    def post_classification(self, code):
        url = reverse(views.ClassificationList.name)
        data = {
            'code': code
        }
        response = self.client.post(url, data, file_format='json')
        return response

    def test_post_and_get_classification(self):
        """
        Проверка создания и получения классификационной группы
        """
        new_classification_code = 'Hexacopter'
        response = self.post_classification(new_classification_code)
        print("PK {0}".format(Classification.objects.get().pk))
        assert response.status_code == status.HTTP_201_CREATED
        assert Classification.objects.count() == 1
        assert Classification.objects.get().code == new_classification_code

    def test_post_existing_classification_code(self):
        """
        Проверка невозможности создания существующей классификационной группы
        """
        url = reverse(views.ClassificationList.name)
        new_drone_category_name = 'Hexacopter repeat'
        data = {'name': new_drone_category_name}
        response1 = self.post_classification(new_drone_category_name)
        assert response1.status_code == status.HTTP_201_CREATED
        response2 = self.post_classification(new_drone_category_name)
        print(response2)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_classification_by_name(self):
        """
        Проверка фильтра классификационных групп по имени
        """
        classification_code1 = 'Hexacopter'
        self.post_classification(classification_code1)
        classification_code2 = 'Octocopter'
        self.post_classification(classification_code2)
        filter_by_code = {'code': classification_code1}
        url = '{0}?{1}'.format(
            reverse(views.ClassificationList.name),
            urlencode(filter_by_code))
        print(url)
        response = self.client.get(url, format='json')
        print(response)
        assert response.status_code == status.HTTP_200_OK
        # Проверяем, что в ответе только один элемент
        assert response.data['count'] == 1
        # Проверяем соотвествие его наименованию фильтру
        assert response.data['results'][0]['name'] == classification_code1
