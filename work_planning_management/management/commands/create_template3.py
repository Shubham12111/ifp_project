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
                            <p><b>Re: Survey of Front Door</b></p>
                            <p>As part of the current fire regulations &amp; your safety, we have been instructed by London Borough of
                                Redbridge, your landlord/housing provider, to survey and replace your front door.</p>
                            <p>We need to survey your Front Door on (insert date) Between (insert time) this will take approximately 10
                                minutes.</p>
                            <p>Following the survey to your front door, we will require you to complete the enclosed door choice form as
                                London Borough of Redbridge has given you a door choice option.</p>
                            <p>Either the door choice form can be handed to the surveyor, or it can be forwarded to our Resident Liaison
                                Officers email address: Alysha@infinityfireprevention.com</p>
                            <p>To enable these works to progress please make contact using one of the following options quoting your
                                property address.</p>
                            <p>1. Phone 0800 112 0404</p>
                            <p>2. Email - Alysha@infinityfireprevention.com</p>
                            <p>Please can you ensure we have this form returned to us within 10 days within receipt of this letter.</p>
                            <p>Should you require verification of this letter please contact Customer Services at London Borough of Redbridge
                                on 020 8554 5000.</p>
                            <p>We would like to apologise in advance for any inconvenience caused but it is necessary for these essential
                                works to be carried out and your co-operation would be greatly appreciated.</p>
                            <p>Yours faithfully,</p>
                            <p><b>The RLO Team</b></p>
                            <p><b>Infinity Fire Prevention LTD</b></p>
       
        """

        # Merge the complete template by concatenating the sections
        complete_template = f"""
        <div class="container">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5 class="card-title">Survey of Front Door</h5>
                               
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
            name='Survey of Front Door',
            site_address_info=site_address_info,
            company_info=company_info,
            main_content_block=main_content_block,
            complete_template = complete_template
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created RLO Letter Template: {template.name}'))

