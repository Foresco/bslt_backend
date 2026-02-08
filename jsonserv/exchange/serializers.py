from rest_framework import serializers
# Классы, подлежащие сериализации


class GeneralSerializer(serializers.ModelSerializer):
    """Универсальный сериалайзер. Требует предварительного указания модели"""

    class Meta:
        model = None
        fields = '__all__'  # По умолчанию выгружаем все поля


def get_model_serializer(model):
    GeneralSerializer.Meta.model = model
    json_fields = getattr(model.BasaltaProps, 'json_fields', '')
    if json_fields:
        GeneralSerializer.Meta.fields = json_fields
    return GeneralSerializer


class ExternalIDSerializer(serializers.Serializer):
    """Сериализатор для ссылок во внешних системах"""
    pk = serializers.IntegerField()
    partner_name = serializers.CharField(source='partner__partner_name')
    header_url = serializers.CharField(source='partner__header_url')
    external_id = serializers.CharField()
