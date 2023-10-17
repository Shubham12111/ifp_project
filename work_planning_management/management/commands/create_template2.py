# management/commands/create_templates.py
from django.core.management.base import BaseCommand
from work_planning_management.models import RLOLetterTemplate

class Command(BaseCommand):
    help = 'Create RLO Letter Templates from HTML data'

    def handle(self, *args, **options):
        # Define HTML data for each section
        site_address_info = """
         <div class="col-12">
                                <img src="https://ifp-static-beta.s3.eu-west-2.amazonaws.com/static/assets/img/logo2.png" alt="Company Logo"  style="max-height: 4rem;">
                            </div>
       <p class="text-wrap">INFINITY FIRE PREVENTION LTD</p>
                            <p class="text-wrap">Infinity House</p>
                            <p class="text-wrap">38verside Sir Thomas Longley Road</p>
                            <p class="text-wrap">Tex</p>
        """

        company_info = """
         <div class="col-12">
                                <img src="https://ifp-static-beta.s3.eu-west-2.amazonaws.com/static/assets/img/logo2.png" alt="Company Logo"  style="max-height: 4rem;">
                            </div>
        <p class="text-wrap">Infinity Fire Prevention Ltd</p>
                            <p class="text-wrap">Infinity House 38 Riverside</p>
                            <p class="text-wrap">Sir Thomas Longley Road</p>
                            <p class="text-wrap">Rochester</p>
                            <p class="text-wrap">Kent</p>
                            <p class="text-wrap">ME2 4DP</p>
        """

        main_content_block = """
        <p><b>Date:</b> 1 November 2022</p>
                            <p>Dear Resident,</p>
                            <p><b>Re: Timber Door Maintenance Works</b></p>
                            <p>As part of the current fire regulations & your safety, we have been instructed by Abri, your landlord/housing provider, to carry out Timber Door Maintenance Works</p>
                            <p>We need to carry out these essential works in your flat entrance at a suitable date and time that convenient for you</p>
                            <p>To enable these works to progress please make contact using one of the following option quoting your property address.</p>
                            <p>1. Phone 0800 1120404</p>
                            <p>2. Email: LO@infinitylineprevention.com</p>
                            <p>Should you require verification of this letter please contact Customer Services at Abri on 0300 123 1567</p>
                            <p>We would like to apologise in advance for any inconvenience caused but it is necessary for these essential works to be carried out and your co-operation would be greatly appreciated.</p>
                            <p>Yours faithfully,</p>
                            <p><b>The RLO Team</b></p>
       
        """

        # Merge the complete template by concatenating the sections
        complete_template = f"""
        <div class="container">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5 class="card-title">Timber Door Maintenance Works</h5>
                               
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-6">
                                    {site_address_info}
                                </div>
                                <div class="col-6" style="text-align: right;">
                                    {company_info}
                                </div>
                            </div>
                            <div class="row mt-4">
                                <div class="col-12">
                                    {main_content_block}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

        # Create an instance of RLOLetterTemplate with the complete template
        template = RLOLetterTemplate.objects.create(
            name='Timber Door Maintenance Works',
            site_address_info=site_address_info,
            company_info=company_info,
            main_content_block=main_content_block,
            complete_template = complete_template
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created RLO Letter Template: {template.name}'))

