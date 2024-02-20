import uuid

from django.utils import timezone

from rest_framework import serializers

from infinity_fire_solutions.aws_helper import upload_signature_to_s3
from infinity_fire_solutions.custom_form_validation import save_pdf_from_html

from customer_management.serializers import ( 
    BillingAddress, BillingAddressSerializer
)
from requirement_management.serializers import (
    RequirementSerializer,
    RequirementDefectListSerializer,
    RequirementReportListSerializer,
    RequirementQuotationListSerializer
)

from invoice_management.models import (
    Invoice,

    # invoice forgien key models 
    Requirement, RequirementDefect, Report, Quotation, User,

    # invoice model status
    INVOICE_STATUS_CHOICES
)

class InvoiceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an Invoice object.

    Attributes:
        requirement (PrimaryKeyRelatedField): The primary key related field for the Requirement object.
        report (PrimaryKeyRelatedField): The primary key related field for the Report object.
        defects (PrimaryKeyRelatedField): The primary key related field for the RequirementDefect objects (many-to-many relationship).
        quotation (PrimaryKeyRelatedField): The primary key related field for the Quotation object.
        total_amount (DecimalField): The total payable amount for the invoice.
        status (ChoiceField): The status of the invoice.

    Meta:
        model (Invoice): The model associated with the serializer.
        fields (tuple): A tuple containing the fields to be included in the serialized representation.

    """

    requirement = serializers.PrimaryKeyRelatedField(
        queryset = Requirement.objects.all(),
        required = True
    )

    report = serializers.PrimaryKeyRelatedField(
        queryset = Report.objects.all(),
        required = True
    )

    defects = serializers.PrimaryKeyRelatedField(
        queryset = RequirementDefect.objects.all(),
        many = True,
        required = True
    )

    quotation = serializers.PrimaryKeyRelatedField(
        queryset = Quotation.objects.all(),
        required = True
    )

    total_amount = serializers.DecimalField(
        max_digits = 10, 
        decimal_places = 2,
        required = True
    )

    status = serializers.ChoiceField(
        choices = INVOICE_STATUS_CHOICES,
        default = 'draft'
    )

    billing_information_json = serializers.PrimaryKeyRelatedField(
        queryset = BillingAddress.objects.all(),
        required = True
    )

    class Meta:
        model = Invoice
        fields = (
            # Requirements (FRA) Relations
            'requirement', 'report', 'defects', 'quotation',
            # Detailed JSON with SOR and Defects
            'invoice_json',
            # Payable Total Amount
            'total_amount',
            # Status of the Invoive
            'status',

            # Additional data for the Invoice PDF
            'billing_information_json'
        )

    def validate_billing_information_json(self, value):
        """
        Validates the billing information JSON.

        Args:
            value (dict): The billing information JSON data.

        Returns:
            dict: The validated billing information JSON data.

        Raises:
            serializers.ValidationError: If the billing information is missing or incomplete.
        """
        # Serialize the billing address data
        billing_information_json = BillingAddressSerializer(value).data
        
        # Check if billing information is missing
        if not billing_information_json:
            raise serializers.ValidationError('The Customer does not have the billing information, please update the billing information before you issue an invoice for the customer.')
        
        # Update company name if available
        billing_information_json.update(
            {'company_name': f'{value.user_id.company_name if value.user_id.company_name else "-"}'}
        )
        return billing_information_json

    def create(self, validated_data):
        """
        Create a new Invoice instance.

        Args:
            validated_data (dict): Validated data for creating the Invoice.

        Returns:
            Invoice: The newly created Invoice instance.

        Raises:
            Any exceptions raised during Invoice creation.

        """
        # Create the Invoice
        instance: Invoice = super().create(validated_data)

        # If the instance status is "submitted" or "sent_to_customer", generate a PDF for the invoice.
        if instance.status in ['submitted', 'sent_to_customer']:
            instance.submitted_at = timezone.now()

            # Form a path for the Invoice file to save
            pdf_path = f'requirement/{instance.requirement.id}/quotation/{instance.quotation.id}/invoice/pdf'
            # Generate a unique file name
            unique_pdf_filename = f"{str(uuid.uuid4())}_quotation_{instance.id}_invoice.pdf"

            # Create the context for the template
            context= {
                'customer_id': instance.customer.id,
                'customer_data': instance.customer,
                'customer_address': instance.billing_information_json,
                'requirement_instance': instance.requirement,
                'quotation': instance.quotation,
                'instance': instance
            }

            # Generate the PDF file from the template
            pdf_file = save_pdf_from_html(context=context, file_name=unique_pdf_filename, content_html='invoice.html')
            
            if pdf_file:
                # Upload the PDF file to the given path
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                # Update the PDF file path of the instance and save the changes.
                instance.pdf_path = f'{pdf_path}/{unique_pdf_filename}'
                instance.save()

        return instance

    def update(self, instance, validated_data):
        """
        Update the Invoice instance.

        Args:
            instance (Invoice): The Invoice instance to update.
            validated_data (dict): The validated data to update.

        Returns:
            Invoice: The updated Invoice instance.

        """
        # Create the Invoice
        instance: Invoice = super().update(instance, validated_data)

        # If the instance status is "submitted" or "sent_to_customer", generate a PDF for the invoice.
        if instance.status in ['submitted', 'sent_to_customer']:
            instance.submitted_at = timezone.now()
            
            # Form a path for the Invoice file to save
            pdf_path = f'requirement/{instance.requirement.id}/quotation/{instance.quotation.id}/invoice/pdf'
            # Generate a unique file name
            unique_pdf_filename = f"{str(uuid.uuid4())}_quotation_{instance.id}_invoice.pdf"

            # Create the context for the template
            context= {
                'customer_id': instance.customer.id,
                'customer_data': instance.customer,
                'customer_address': instance.billing_information_json,
                'requirement_instance': instance.requirement,
                'quotation': instance.quotation,
                'instance': instance
            }

            # Generate the PDF file from the template
            pdf_file = save_pdf_from_html(context=context, file_name=unique_pdf_filename, content_html='invoice.html')
            
            if pdf_file:
                # Upload the PDF file to the given path
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                # Update the PDF file path of the instance and save the changes.
                instance.pdf_path = f'{pdf_path}/{unique_pdf_filename}'
                instance.submitted_at = timezone.now()
                instance.save()

        return instance

class InvoiceListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Invoice instances.
    """

    class Meta:
        model = Invoice
        fields = '__all__'

    def to_representation(self, instance: Invoice):
        """
        Convert Invoice instance to representation.

        Args:
            instance (Invoice): The Invoice instance to represent.

        Returns:
            dict: The representation of the Invoice instance.

        """
        data = super().to_representation(instance)
        data['requirement'] = RequirementSerializer(instance.requirement).data if instance.requirement else {}
        data['defects'] = RequirementDefectListSerializer(instance.defects.all(), many=True).data if instance.defects.all() else {}
        data['report'] = RequirementReportListSerializer(instance.report).data if instance.report else {}
        data['quotation'] = RequirementQuotationListSerializer(instance.quotation) if instance.quotation else {}
        data['user'] = instance.user
        data['status'] = instance.get_status_display() if instance.status else ''
        data['submitted_at'] = instance.submitted_at.strftime("%d/%m/%Y") if instance.submitted_at else ''
        data['created_at'] = instance.created_at.strftime("%d/%m/%Y")
        return data