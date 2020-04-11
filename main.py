from pprint import pprint
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition)

import base64
import csv
import vobject
import json
import os

load_dotenv()


class ContactFileParser:

    def __init__(self, student_csv='students', ol_csv=None):
        """Load csv file {students}.csv and then parse the contacts"""
        self.students = self.parse_student_csv(student_csv)

        if ol_csv:
            self.ols = self.parse_ol_csv(ol_csv)
        else:
            self.ols = {}

            # now that we've loaded students, generate dictionary of OLs
            self.parse_ol_from_students()

    def parse_ol_from_students(self):
        for number, group in enumerate(self.students.values()):
            # ol group number
            ol_group = int(number) + 1

            # grab first student in the group to parse info from
            student = group[0]

            # retrieve basic data
            ol = student['OL Name']
            flag = student['Flag']

            self.ols[ol_group] = {'OL Name': ol,
                                  'Flag': flag, 'Group Number': ol_group}

    def process_students(self):
        ol_groups = set(self.ols.keys())
        student_groups = set(self.students.keys())

        # build a list of the group numbers for which there are
        # students and an OL for those students
        groups = student_groups.intersection(ol_groups)

        for group in groups:
            ol = self.ols[group]
            students = self.students[group]

            print(">>> Creating Group Contact Files for [{}] {}".format(
                ol['Flag'], ol['OL Name']))
            vobjects = []

            for student in students:
                family_name = student['Last']
                given_name = student['First']
                fn = '{} {}'.format(given_name, family_name)
                email = student['MIT Email'].lower()
                phone = student['Cell Phone']
                category = F'''{ol['Flag']} {group} First Year'''

                j = vobject.vCard()
                j.add('n')
                j.n.value = vobject.vcard.Name(
                    family=family_name, given=given_name)

                j.add('fn')
                j.fn.value = fn

                if email != '':
                    j.add('email')
                    j.email.value = email

                if phone != 'N/A':
                    j.add('tel')
                    j.tel.value = phone

                j.add('org')
                j.org.value = [category]

                vobjects.append(j)

                # print(j.serialize())

            self.create_vcf_file(ol, vobjects)

    @staticmethod
    def create_vcf_file(ol, contacts):
        file_name = F'''contact-files/{ol['Flag']}_{ol['Group Number']}_{ol['OL Name'].replace(' ', '_')}.vcf'''

        if not os.path.isfile(file_name):
            with open(file_name, 'w') as contact_file:
                for contact in contacts:
                    contact_file.write(contact.serialize())
        else:
            print('file already exists')

        # uncomment if you don't want to send
        # ContactFileParser.send_vcf_file(ol, file_name)

    @staticmethod
    def send_vcf_file(ol, file_path):
        ol_email = ol['Kerberos']

        message = Mail(
            from_email='dangonzo@mit.edu',
            to_emails=ol_email,
            subject='Here is your OL contact file! 🎉',
            html_content=F'''Hi {ol['First Name']},<br/><br/>
                Attached to this email is a file containing the contact information 
                for all of your First Year Students. Some of them may not have phone
                numbers or emails, but they definitely have at least one. If, for some
                reason, a contact doesn't have either an email or a phone number, please
                reach out to either Chelsea or Taylor (or myself, since I have the data)<br/><br/>
                <b>How to install contacts on iPhone</b><br/>
                If you have an iPhone, all you need to do to install the contacts is to click
                on the attachment in this email. Then, a window should pop up on your screen
                that says information about only one contact, ignore this and click the <em>share</em>
                button in the top right hand corner and then select the option 'Copy to Contacts'.
                Then, just make sure to click the option that says "Add all n contacts" and there you go!
                <br/><br/>
                Assuming all works well and my code isn't jank, you should be able to search 
                for your first years in the Contacts app by looking up "Blue 13" (if you are the OL
                for group Blue 13). Feel free to create your own contact group!
                <br/><br/>
                <b>How to install contacts on Android</b><br/>
                For the first time in all of human history, android is better at something 
                than iPhone. All you need to do is click on the attachment and android
                will import the contacts and even create a contact group for you named 
                '#Color #Number First Year'
                <br/><br/>
                Please let me know if something does not work!
                <br/><br/>
                Best,
                <br/><br/>
                Gonzo''')

        with open(file_path, 'rb') as f:
            data = f.read()

        encoded = base64.b64encode(data).decode()

        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType('text/x-vcard')
        attachment.file_name = FileName(
            file_path.replace('contact-files/', ''))
        attachment.disposition = Disposition('attachment')
        message.attachment = attachment

        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(str(e))

    @staticmethod
    def parse_ol_csv(name):
        path = name + '.csv'

        info = []
        with open(path) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')

            for row in reader:

                info.append(list(row))

        headers = [n.replace(u'\ufeff', '') for n in info[0]]
        ols = info[1:]

        ol_jsons = {}
        for ol in ols:
            ol_json = {}
            for key, value in zip(headers, ol):
                ol_json[key] = value

            ol_json['OL Name'] = F'''{ol_json['First Name']} {ol_json['Last Name']}'''
            try:
                ol_number = int(ol_json['Group Number'])
                ol_jsons[ol_number] = ol_json
            except KeyError as e:
                raise e(
                    "There must be an 'Group Number' Column for the students and the OL's")

        return ol_jsons

    @staticmethod
    def parse_student_csv(name):
        path = name + '.csv'

        info = []
        with open(path) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')

            for row in reader:

                info.append(list(row))

        headers = [n.replace(u'\ufeff', '') for n in info[0]]
        students = info[1:]

        student_jsons = {}
        for student in students:
            student_json = {}
            for key, value in zip(headers, student):
                student_json[key] = value

            try:
                ol_number = int(student_json['OL Number'])
                if ol_number in student_jsons:
                    student_jsons[ol_number].append(student_json)
                else:
                    student_jsons[ol_number] = [student_json]
            except KeyError as e:
                raise e(
                    "There must be an 'OL Number' Column for the students and the OL's")

        return student_jsons


if __name__ == "__main__":
    print('Welcome to tool')
    c = ContactFileParser(student_csv='data', ol_csv='ols')
    print(c.ols)
    c.process_students()
