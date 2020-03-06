from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
class FDFSStorage(Storage):
    # fdfs文件存储
    def _open(self, name, mode='rb'):
        pass
    def _save(self, name, content):
        # name:你选择的上传文件名字
        # content：包含你上传文件内容的file对象

        # 创建一个Fdfs_clier对象
        client = Fdfs_client('./utils/fdfs/client.conf')

        # 上传文件到fastdfs中
        res = client.upload_appender_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get('Status') != 'Upload Successed.':
            # 上传失败
            raise Exception('上传文件到fast_dfs失败')
        filename = res.get('Remote file_id')
        return filename
    def exists(self, name):
        '''判断文件名是否可用'''
        return False
    def url(self, name):
        return name