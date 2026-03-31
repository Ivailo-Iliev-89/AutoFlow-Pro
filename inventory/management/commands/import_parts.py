import pandas as pd
from django.core.management.base import BaseCommand
from inventory.models import Brand, Part


class Command(BaseCommand):
    help = 'Importing parts of Excel file'

    def add_arguments(self, parser):
        '''Takes a file name as an argument'''
        parser.add_argument('file_path', type=str,
                            help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            df = pd.read_excel(file_path)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully loaded file: {file_path}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error to reading a file: {e}'))
            return

        for index, row in df.iterrows():
            try:
                # If Brand not excists --> then created
                brand_obj, created = Brand.objects.get_or_create(
                    name=row['Brand'])

                # If Part is in the list --> Ddding a price and qty/ if not --> then created
                part, created = Part.objects.update_or_create(
                    oem_num=row['OEM'],
                    defaults={
                        'brand': brand_obj,
                        'name': row['Name'],
                        'purchase_price': row['Price'],
                        # Automatic 20 % Markup
                        'sale_price': float(row['Price']) * 1.2,
                        'stock_qty': row['Qty'],
                    }
                )

                status = 'Created' if created else 'Updated'
                self.stdout.write(f'{status} part : {part.oem_num}')

            except KeyError as e:
                self.stdout.write(self.style.ERROR(
                    f'Missing column in Excel: {e}'))
                break
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Row {index} skipped: {e}'))
