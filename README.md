# easyContact
A tool for uploading a CSV that can be parsed to create a Group vCard (virtual contact card) file that can be emailed to Orientation Leaders for easy adding contacts to phone

## setup
Virtual Environment Setup
```
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

## general "how it works"

For the `ContactFileParser` class, it takes in a path for a csv file (without the csv lol) for both `student_csv` and `ol_csv`, so students are the contact information that I group up to send to the OLs, which are contained in the `ol_csv`. The parsing is pretty specific to Orientation, so you can just read through that and see how it works and change it up to your use case. Then it creates the VCF files and stores them locally (you might need to manually create a `/contact-files` directory if you want to keep this functionality), and then uses [Sendgrid](https://sendgrid.com) to send it!



