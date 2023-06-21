import barcode
import cx_Oracle
import io
import jinja2
import os
import pdfkit

from barcode.writer import ImageWriter
from barcode.base import Barcode
from datetime import date, datetime

from config import Config


BASE_PATH = os.getcwd() 


def makeDictFactory(cursor):
    columnNames = [d[0] for d in cursor.description]
    def createRow(*args):
       return dict(zip(columnNames, args))
    return createRow

if __name__=='__main__':
    conn = cx_Oracle.connect(user=Config.DATABASE_USER, password=Config.DATABASE_PASSWORD, dsn=Config.DATABASE_DSN)
    curr = conn.cursor()
    
    # print(data.fetchone())
    bill_html = ''
    bill_duplicate_html = ''
    # curr.execute("BEGIN PROCESS_INVOICE(); END;")
    # x
    zones = curr.execute("SELECT ZONE_CODE FROM ZONE").fetchall()
    wards = curr.execute("SELECT WARD_CODE FROM WARD").fetchall()

    for zone in zones:
        current_zone_path = os.path.join(BASE_PATH, f'ZONE_{zone[0]}')
        os.makedirs(current_zone_path, exist_ok=True)
        for ward in wards:
            current_ward_path = os.path.join(current_zone_path, f'ward_{ward[0]}')
            os.makedirs(current_ward_path, exist_ok=True)
            query = f"""SELECT CONSUMER_NAME, CONSUMER_ADDRESS, ISSUE_DATE, DUE_DATE, BILLING_MONTH, CONSUMER_TARRIF_CODE,CONSUMER_DIA, 
                                BILLING_STATUS, NOTICE, CURRENT_WATER_CHARGES, CURRENT_SEWERAGE_CHARGES, CURRENT_CONSTRUCTION_CHARGES, WATER_TARIFF,
                                ARREARS_WATER_CHARGES, SEWERAGE_TARIFF,ARREARS_SEWERAGE_CHARGES, CONSTRUCTION_TARIFF, ARREARS_CONSTRUCTION_CHARGES, 
                                CONSUMER_SERVICE_CHARGES, OUTSTANDING_WATER_ARREARS, WITHIN_DUEDATE_AMOUNT,OUTSTANDING_SEWERAGE_ARREARS, 
                                OUTSTANDING_CONSTRUCTION_ARREARS, CONSUMER_SURCHARGE, OUTSTANDING_TOTAL,AFTER_DUEDATE_AMOUNT, 
                                PRIMARY_CONSUMER_NO, CONSUMER_NO, CURRENT_TOTAL, ARREARS_TOTAL_CHARGES  FROM INVOICE WHERE CONSUMER_ZONE_NO LIKE '%{zone[0]}%' 
                                AND CONSUMER_WARD_NO LIKE '%{ward[0]}%' AND ROWNUM < 2"""
            print(query)
            data = curr.execute(query)
            curr.rowfactory = makeDictFactory(curr)
            
            for idx, row in enumerate(data.fetchall()):
                print(idx)
                print(row['CONSUMER_NO'])
                query1 = f"""SELECT BILLING_MONTH, AMOUNT FROM PAYMENT_HISTORY 
                            WHERE CONSUMER_NO = '{row["CONSUMER_NO"]}' AND ROWNUM < 13 
                            ORDER BY TO_DATE(BILLING_MONTH, 'MM-YY') DESC"""
            
                row['PAYMENT_HISTORY'] = curr.execute(query1).fetchall()                
                
                for key, cell in row.items():
                    if isinstance(cell, datetime):
                        row[key] = cell.strftime('%d/%m/%Y')
                    if isinstance(cell, str):
                        row[key] = row[key].strip()
                barcode_path = os.path.join(BASE_PATH, 'barcode')
                barcode.generate('code39', f'{row["CONSUMER_NO"]} {row["WITHIN_DUEDATE_AMOUNT"]} {row["DUE_DATE"]} {row["AFTER_DUEDATE_AMOUNT"]}', writer=ImageWriter() , text=row["CONSUMER_NO"], output=barcode_path)
                row['BARCODE'] = f"{barcode_path}.png"
                bill_html += jinja2.Environment(  
                                loader = jinja2.FileSystemLoader(searchpath=BASE_PATH)).get_template(
                                'bill_tamplate.html').render(date=date.today().strftime('%d/%m/%Y'), df=row
                            )

                
                bill_duplicate_html += jinja2.Environment(  
                                        loader = jinja2.FileSystemLoader(searchpath=BASE_PATH)).get_template(
                                        'bill_duplicate.html').render(date=date.today().strftime('%d/%m/%Y'), df=row
                                        )
                                 
            file_name = os.path.join(current_ward_path, f'{ward[0]}.pdf')
            duplicate_file_name = os.path.join(current_ward_path, f'{ward[0]}_duplicate.pdf')
            print(file_name)
            print(duplicate_file_name)
            pdfkit.from_string(bill_html, file_name)
            pdfkit.from_string(bill_duplicate_html, duplicate_file_name)
