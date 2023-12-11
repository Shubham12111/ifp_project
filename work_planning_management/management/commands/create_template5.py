# management/commands/create_templates.py
from django.core.management.base import BaseCommand
from work_planning_management.models import RLOLetterTemplate

class Command(BaseCommand):
    help = 'Create RLO Letter Templates from HTML data'

    def handle(self, *args, **options):
        # Define HTML data for each section
        site_address_info = """
         <div class="col-12">
                                <img src="https://ifp-static-dev.s3.eu-west-2.amazonaws.com/static/assets/img/logo2.png" alt="Company Logo"  style="max-height: 4rem;">
                            </div>
    <p class="text-wrap">The Resident</p>
                            <p class="text-wrap">Flat 1</p>
                            <p class="text-wrap">Antler House</p>
                            <p class="text-wrap">Kielder Close</p>
                            <p class="text-wrap">Ilford</p>
                            <p class="text-wrap">IG6 3ER</p>
        """

        company_info = """
         <div class="col-12">
                                <img src="https://ifp-static-dev.s3.eu-west-2.amazonaws.com/static/assets/img/logo2.png" alt="Company Logo"  style="max-height: 4rem;">
                            </div>
         <p class="text-wrap">Infinity Fire Prevention Ltd</p>
                            <p class="text-wrap">Infinity House 38 Riverside</p>
                            <p class="text-wrap">Sir Thomas Longley Road</p>
                            <p class="text-wrap">Rochester</p>
                            <p class="text-wrap">Kent</p>
                            <p class="text-wrap">ME2 4DP</p>
        """

        main_content_block = """
        <p><b>Date:</b> 9th March 2023,</p>
                            <p>Dear Resident,</p>
                            <p><b>Re: Front Door Replacement</b></p>
                            <p>As part of the current fire regulations &amp; your safety, we have been instructed by Peabody, your
                                landlord/housing provider, to replace your front entrance door.</p>
                            <p>Thank you for your assistant with the survey and door choice forms.</p>
                            <p>We need to install your new flat entrance door on «day_» «date_» «Month» 2023 Between «Time_»
                                this will take approximately 4 Hours.</p>
                            <p>To enable these works to progress please make contact using one of the following options quoting your
                                property address.</p>
                            <p>Phone - 0800 112 0404</p>
                            <p>Email – Terri.Roper@Sureserve-fe.co.uk</p>
                            
                            <p>We would like to apologise in advance for any inconvenience caused but it is necessary for these
                                essential works to be carried out and your co-operation would be greatly appreciated.</p>
                            <p>Yours faithfully,</p>
                            <p><b>The RLO Team</b></p>
                            <p><b>Sureserve Fire &amp; Electrical</b></p>
       
        """

        # Merge the complete template by concatenating the sections
        complete_template = f"""
        <div class="container">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5 class="card-title">Front Door Replacement</h5>
                                
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
            name='Front Door Replacement',
            site_address_info=site_address_info,
            company_info=company_info,
            main_content_block=main_content_block,
            complete_template = complete_template
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created RLO Letter Template: {template.name}'))

