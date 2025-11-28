from products.dbio import ImportJobDbIO


class ImportJobHandler:
    
    def get_job_status(self, job_uuid):
        import_job_dbio = ImportJobDbIO()
        
        try:
            import_job = import_job_dbio.get_obj({'uuid': job_uuid})
            
            return {
                'job_id': str(import_job.uuid),
                'status': import_job.status,
                'progress': import_job.progress,
                'total_records': import_job.total_records,
                'processed_records': import_job.processed_records,
                'successful_records': import_job.successful_records,
                'failed_records': import_job.failed_records,
                'file_name': import_job.file_name,
                'file_size': import_job.file_size,
                'error_message': import_job.error_message,
                'started_at': import_job.started_at.isoformat() if import_job.started_at else None,
                'completed_at': import_job.completed_at.isoformat() if import_job.completed_at else None,
                'duration': import_job.duration,
            }
        except import_job_dbio.model.DoesNotExist:
            raise ValueError(f"Import job with ID {job_uuid} not found")

