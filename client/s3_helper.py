# def check_folder_exists(client, folder_path: str, bucket_name: str) -> bool:
#     if not folder_path.endswith('/'):
#         folder_path += '/'
    
#     resp = client.list_objects(Bucket=bucket_name, Prefix=folder_path, Delimiter='/',MaxKeys=1)
#     return 'Contents' in resp

def upload_file_to_folder(client, folder_path: str, bucket_name: str, local_file_path: str, name_of_file_for_bucket: str):
    if not folder_path.endswith('/'):
        folder_path += '/'
    try:
        client.upload_file(local_file_path, bucket_name, '%s%s' % (folder_path, name_of_file_for_bucket))
    except Exception as e:
        print(f"Error uploading file to S3: {e}")

def count_files_in_folder(client, folder_path: str, bucket_name: str) -> int:
    if not folder_path.endswith('/'):
        folder_path += '/'
    object_count = 0
    paginator = client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_path)

    for page in pages:
        if 'Contents' in page:
            object_count += len(page['Contents'])

    return object_count



