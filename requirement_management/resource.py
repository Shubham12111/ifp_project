
from django.utils import timezone
from datetime import datetime
from import_export import resources
from import_export.results import RowResult
from django.db import transaction
from .models import SORItem

class SORItemUpload(resources.ModelResource):
    class Meta:
        model = SORItem

    def save_instance(self, instance, using_transactions=True, dry_run=False, **kwargs):
        """
        Override the save_instance method to handle bulk create and bulk update.
        """
        if using_transactions and not dry_run:
            # Set created_at if it's not set in the import file
            if not instance.created_at:
                instance.created_at = timezone.now()

            # Check if an object with the same reference_number exists
            existing_instance = self.get_existing_instance(instance)

            if existing_instance:
                # If exists, update the existing instance
                instance.pk = existing_instance.pk
                super().save_instance(instance, using_transactions, dry_run, **kwargs)
                self.update_instances.append(instance)
            else:
                # If doesn't exist, perform regular save
                super().save_instance(instance, using_transactions, dry_run, **kwargs)
                self.create_instances.append(instance)

    def get_existing_instance(self, instance):
        """
        Check if an object with the same reference_number already exists.
        """
        reference_number_field = self.fields['reference_number']
        filter_kwargs = {reference_number_field.column_name: instance.reference_number}
        return SORItem.objects.filter(**filter_kwargs).first()

    def after_import(self, dataset, using_transactions, dry_run, result, **kwargs):
        """
        Override the after_import method to perform bulk create and bulk update.
        """
        super().after_import(dataset, using_transactions, dry_run, result, **kwargs)
        
        # Perform bulk create and bulk update
        if not dry_run:
            batch_size = self.get_chunk_size()
            self.bulk_create(using_transactions, dry_run, raise_errors=True, batch_size=batch_size)
            self.bulk_update(using_transactions, dry_run, raise_errors=True, batch_size=batch_size)


    def after_import(self, dataset, using_transactions, dry_run, result, **kwargs):
        """
        Override the after_import method to perform bulk create and bulk update.
        """
        super().after_import(dataset, using_transactions, dry_run, result, **kwargs)
        
        # Perform bulk create and bulk update
        if not dry_run:
            batch_size = self.get_chunk_size()
            self.bulk_create(using_transactions, dry_run, raise_errors=True, batch_size=batch_size)
            self.bulk_update(using_transactions, dry_run, raise_errors=True, batch_size=batch_size)
