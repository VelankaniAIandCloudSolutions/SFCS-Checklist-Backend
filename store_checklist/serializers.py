from rest_framework import serializers
from .models import *
from accounts.serializers import UserAccountSerializer


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'


class ManufacturerPartSerializer(serializers.ModelSerializer):
    manufacturer = ManufacturerSerializer()

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
    references = BillOfMaterialsLineItemReferenceSerializer(many=True)

    class Meta:
        model = BillOfMaterialsLineItem
        fields = '__all__'


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    bom_type = BillOfMaterialsTypeSerializer()
    bom_line_items = BillOfMaterialsLineItemSerializer(many=True)
    product = ProductSerializer()
    issue_date = serializers.DateField(format="%d/%m/%Y")

    # references = serializers.SerializerMethodField()

    class Meta:
        model = BillOfMaterials
        fields = '__all__'

    # def get_references(self, obj):
    #     # Extract the references from bom_line_items and flatten the list
    #     references_list = [ref for item in obj.bom_line_items.all()
    #                        for ref in item.references.all()]

    #     # Serialize the references
    #     return BillOfMaterialsLineItemReferenceSerializer(references_list, many=True).data


class BillOfMaterialsDetailedSerializer(serializers.ModelSerializer):
    bom_type = BillOfMaterialsTypeSerializer()
    bom_line_items = BillOfMaterialsLineItemSerializer(many=True)
    product = ProductSerializer()
    issue_date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = BillOfMaterials
        fields = '__all__'


class ChecklistItemTypeSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = ChecklistItemType
        fields = '__all__'


class ChecklistItemSerializer(serializers.ModelSerializer):
    bom_line_item = BillOfMaterialsLineItemSerializer()
    checklist_item_type = ChecklistItemTypeSerializer()
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = ChecklistItem
        fields = '__all__'


class ChecklistSerializer(serializers.ModelSerializer):
    checklist_items = serializers.SerializerMethodField()
    bom = BillOfMaterialsSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    created_by = UserAccountSerializer()
    updated_by = UserAccountSerializer()

    class Meta:
        model = Checklist
        fields = '__all__'

    def get_checklist_items(self, obj):
        checklist_items = obj.checklist_items.order_by('-updated_at')
        serializer = ChecklistItemSerializer(checklist_items, many=True)
        return serializer.data


class ChecklistSettingSerializer(serializers.ModelSerializer):
    active_bom = BillOfMaterialsSerializer()

    class Meta:
        model = ChecklistSetting
        fields = '__all__'
