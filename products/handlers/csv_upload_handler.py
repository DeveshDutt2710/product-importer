from products.choices import ImportJobStatuses
from products.dbio import ImportJobDbIO
from products.handlers.file_handler import (
    save_uploaded_file_to_temp, 
    validate_csv_file
)
from products.tasks import process_csv_import


class CsvUploadHandler:
    
    def upload_csv_file(self, uploaded_file):
        validate_csv_file(uploaded_file)
        
        temp_file_path = save_uploaded_file_to_temp(uploaded_file)
        
        import_job_dbio = ImportJobDbIO()
        import_job = import_job_dbio.create_obj({
            'status': ImportJobStatuses.PENDING,
            'file_name': uploaded_file.name,
            'file_size': uploaded_file.size,
            'total_records': 0,
            'progress': 0,
        })
        
        process_csv_import.delay(str(import_job.uuid), temp_file_path)
        
        return {
            'job_id': str(import_job.uuid),
            'status': import_job.status,
            'file_name': import_job.file_name,
            'file_size': import_job.file_size,
        }

