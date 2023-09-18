from django import template
from django.db.models import Sum
from ..models import RequirementDefect
from infinity_fire_solutions.aws_helper import *

register = template.Library()

@register.filter
def get_defect_action(defect_id):
    defect_action = RequirementDefect.objects.filter(pk=defect_id).first()
    if defect_action:
        return defect_action.action
    else:
        return ""

@register.filter
def get_defect_rectification(defect_id):
    defect_rectification = RequirementDefect.objects.filter(pk=defect_id).first()
    if defect_rectification:
        return defect_rectification.rectification_description
    else:
        return ""


@register.filter
def get_quotation_pdf_path(pdf_path):
    pdf_url =  generate_presigned_url(pdf_path)
    return pdf_url