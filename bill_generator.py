import cx_Oracle
import jinja2
import pdfkit

from datetime import date, datetime

from config import Config


def makeDictFactory(cursor):
    columnNames = [d[0] for d in cursor.description]
    def createRow(*args):
       return dict(zip(columnNames, args))
    return createRow

if __name__=='__main__':
    conn = cx_Oracle.connect(user=Config.DATABASE_USER, password=Config.DATABASE_PASSWORD, dsn=Config.DATABASE_DSN)
    curr = conn.cursor()
    

    data = curr.execute(f"SELECT * FROM INVOICE WHERE ROWNUM < 10")
    curr.rowfactory = makeDictFactory(curr)
    # print(data.fetchone())
    bill_html = ''
    bill_duplicate_html = ''
    for idx, row in enumerate(data.fetchall()):
        print(idx)
        for key, cell in row.items():
            if isinstance(cell, datetime):
                row[key] = cell.strftime('%d/%m/%Y')
            if isinstance(cell, str):
                row[key] = row[key].strip()
        bill_html += jinja2.Environment(  
        loader=jinja2.FileSystemLoader(searchpath='/home/tp-04/Music/bill_generator')).get_template(
        'bill_tamplate.html').render(date=date.today().strftime('%d/%m/%Y'),
                                    df=row)

        bill_duplicate_html += jinja2.Environment(  
        loader=jinja2.FileSystemLoader(searchpath='/home/tp-04/Music/bill_generator')).get_template(
        'bill_duplicate.html').render(date=date.today().strftime('%d/%m/%Y'),
                                    df=row)
        # html = jinja2.Environment(  
        # loader=jinja2.FileSystemLoader(searchpath='/home/tp-04/Music/bill_generator')).get_template(
        # 'bill_tamplate.html').render(date=date.today().strftime('%d/%m/%Y'),
        #                             df=row)

        # html2 = jinja2.Environment(  
        # loader=jinja2.FileSystemLoader(searchpath='/home/tp-04/Music/bill_generator')).get_template(
        # 'bill_duplicate.html').render(date=date.today().strftime('%d/%m/%Y'),
        #                             df=row)
        # if row.get('CONSUMER_NO') == '05-04-02575-0-D':
        #     with open('html_report_jinja.html', 'w+') as f:
        #         f.write(html)
        # with open('bill_duplicate_jinja.html', 'a+') as f:
        #     f.write(html2)
        # Convert HTML to PDF
        # with open(f', "w+b") as out_pdf_file_handle:
        # HTML('/home/tp-04/Music/bill_generator/html_report_jinja.html').write_pdf(f'/home/tp-04/Music/bill_generator/{data.fetchone().get("CONSUMER_NO")}.pdf')
        # for i in range(1,11):
    pdfkit.from_string(bill_html, f'/home/tp-04/Music/bill_generator/bill.pdf')
    pdfkit.from_string(bill_duplicate_html, f'/home/tp-04/Music/bill_generator/bill_duplicate.pdf')
