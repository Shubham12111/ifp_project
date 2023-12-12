# management/commands/create_templates.py
from django.core.management.base import BaseCommand
from work_planning_management.models import RLOLetterTemplate
import os
from django.apps import apps

class Command(BaseCommand):
    help = 'Create RLO Letter Templates from HTML data'

    def handle(self, *args, **options):
        # Define the output folder for generated HTML files
        # output_folder = 'sample_letters'

        # Create the output folder if it doesn't exist
        # os.makedirs(output_folder, exist_ok=True)
        # Define HTML data for each section
        site_address_info = """
         <div class="col-12">
                                <img src="https://ifp-static-beta.s3.eu-west-2.amazonaws.com/static/assets/img/logo2.png" alt="Company Logo"  style="max-height: 4rem;">
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
        <p><b>Date:</b> 9th March 2023,</p>
                            <p>Dear Resident,</p>
                            <p><b>Re: Communal Fire Safety Works</b></p>
                            <p>As part of the current fire regulations &amp; your safety, we have been instructed by Thanet District
                                Council, your landlord/housing provider, to carry out Fire Safety Works in your Communal Loft
                                Spaces.</p>
                            <p>We need to carry out these essential Fire Safety Works in your Communal Loft Spaces and work will
                                commence from 29 th August 2023. We do not need to access the Loft spaces via your Flat Entrance
                                but there may be some noise caused by the works.</p>
                            <p>If you have any questions, please contact us on:</p>
                            <p>Either the door choice form can be handed to the surveyor, or it can be forwarded to our Resident Liaison
                                Officers email address: Alysha@infinityfireprevention.com</p>
                          
                            <p>Email: Terri.roper@sureserve-fe.co.uk</p>
                            <p>Phone: 0800 112 0404</p>
                            <p>Should you require verification of this letter please contact Customer Services at Thanet District
                                Council on 01843 577000</p>
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
                                <h5 class="card-title">Communal without appointment thanet</h5>
                    
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
            name='Communal without appointment thanet',
            site_address_info=site_address_info,
            company_info=company_info,
            main_content_block=main_content_block,
            complete_template = complete_template
        )
        # # Generate the HTML file and save it to the output folder
        # output_filename = os.path.join(output_folder, f'{template.name}.html')
        # with open(output_filename, 'w', encoding='utf-8') as output_file:
        #     output_file.write(complete_template)


        self.stdout.write(self.style.SUCCESS(f'Successfully created RLO Letter Template: {template.name}'))
        # self.stdout.write(self.style.SUCCESS(f'Successfully generated HTML page: {output_filename}'))

