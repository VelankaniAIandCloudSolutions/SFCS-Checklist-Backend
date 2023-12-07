from rest_framework import serializers
from .models import *

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'

class ManufacturerPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturerPart
        fields = '__all__'

class AssemblyStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssemblyStage
        fields = '__all__'

class BillOfMaterialsTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterialsType
        fields = '__all__'

class BillOfMaterialsLineItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterialsLineItemType
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class BillOfMaterialsLineItemReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterialsLineItemReference
        fields = '__all__'

class BillOfMaterialsLineItemSerializer(serializers.ModelSerializer):
    manufacturer_parts = ManufacturerPartSerializer(many=True)
    assembly_stage = AssemblyStageSerializer()
    line_item_type = BillOfMaterialsLineItemTypeSerializer()

    class Meta:
        model = BillOfMaterialsLineItem
        fields = '__all__'

class BillOfMaterialsSerializer(serializers.ModelSerializer):
    bom_type = BillOfMaterialsTypeSerializer()
    lines = BillOfMaterialsLineItemSerializer(many=True)

    class Meta:
        model = BillOfMaterials
        fields = '__all__'

class ChecklistItemSerializer(serializers.ModelSerializer):
    bom_line_item = BillOfMaterialsLineItemSerializer()

    class Meta:
        model = ChecklistItem
        fields = '__all__'

class ChecklistSettingSerializer(serializers.ModelSerializer):
    active_bom = BillOfMaterialsSerializer()

    class Meta:
        model = ChecklistSetting
        fields = '__all__'
