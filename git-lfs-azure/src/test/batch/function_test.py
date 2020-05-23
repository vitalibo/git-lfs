import unittest
from datetime import datetime
from unittest import mock

from azure.storage.blob import BlobPermissions

from batch import function

RFC3339_REGEX = r'^([0-9]+)-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)(\.[0-9]+)?(([Zz])|([\+|\-]([01][0-9]|2[0-3]):[0-5][0-9]))$'


class BlobLargeFileStorageTestCase(unittest.TestCase):

    @mock.patch('azure.storage.blob.blockblobservice.BlockBlobService')
    def setUp(self, mock_blockblobservice):
        self.mock_client = mock.MagicMock()
        mock_blockblobservice.return_value = self.mock_client
        self.lfs = function.BlobLargeFileStorage(
            {
                'STORAGE_ACCOUNT': 'StorageAccountName',
                'STORAGE_ACCOUNT_PRIMARY_KEY': 'StorageAccountPrimaryKeyId',
                'STORAGE_CONTAINER': 'StorageContainerName'
            }
        )

    def test_exists(self):
        self.mock_client.exists.return_value = True

        actual = self.lfs.exists('happyface.jpg')

        self.assertTrue(actual)
        self.mock_client.exists.assert_called_once_with('StorageContainerName', 'happyface.jpg')

    def test_not_exists(self):
        self.mock_client.exists.return_value = False

        actual = self.lfs.exists('happyface.jpg')

        self.assertFalse(actual)
        self.mock_client.exists.assert_called_once_with('StorageContainerName', 'happyface.jpg')

    def test_generate_blob_shared_access_signature_url(self):
        self.mock_client.generate_blob_shared_access_signature.return_value = 'ZA1XSW2EDC'
        expiry = datetime.fromtimestamp(1590558507)

        actual = self.lfs.generate_blob_shared_access_signature_url(
            'happyface.jpg', BlobPermissions.WRITE, expiry
        )

        self.assertEqual(
            actual, 'https://StorageAccountName.blob.core.windows.net/StorageContainerName/happyface.jpg?ZA1XSW2EDC')
        self.mock_client.generate_blob_shared_access_signature.assert_called_once_with(
            'StorageContainerName', 'happyface.jpg', BlobPermissions.WRITE, expiry)

    def test_prepare_download(self):
        with mock.patch('batch.function.BlobLargeFileStorage.generate_blob_shared_access_signature_url') as mock_method:
            mock_method.return_value = 'https://example.com'

            actual = self.lfs.prepare_download('happyface.jpg', 123)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.href, 'https://example.com')
            self.assertRegex(actual.expires_at, RFC3339_REGEX)

    def test_prepare_upload(self):
        with mock.patch('batch.function.BlobLargeFileStorage.generate_blob_shared_access_signature_url') as mock_method:
            mock_method.return_value = 'https://example.com'

            actual = self.lfs.prepare_upload('happyface.jpg', 123)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.href, 'https://example.com')
            self.assertRegex(actual.expires_at, RFC3339_REGEX)
            self.assertEqual(actual.header.get('x-ms-blob-type'), 'BlockBlob')


class KeyInsensitiveDictTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.dictionary = function.KeyInsensitiveDict(
            {
                'foo': 'bar'
            }
        )

    def test_getitem(self):
        actual = self.dictionary['Foo']

        self.assertEqual(actual, 'bar')

    def test_get(self):
        actual = self.dictionary.get('Foo')

        self.assertEqual(actual, 'bar')

    def test_get_missing_value(self):
        actual = self.dictionary.get('baz')

        self.assertIsNone(actual)


class FunctionTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_request = mock.MagicMock()
        self.mock_request.url = 'https://foo.com/api/objects/batch'
        self.mock_context = mock.MagicMock()
        self.mock_context.invocation_id = 'uuid'
        self.mock_response = mock.MagicMock()
        self.mock_facade = mock.MagicMock()

    def test_main(self):
        with mock.patch('batch.function.process') as mock_process_method:
            mock_process_method.return_value = self.mock_response

            actual = function.main(self.mock_request, self.mock_context)

            self.assertEqual(actual, self.mock_response)
            mock_process_method.assert_called_once_with(self.mock_request, self.mock_context)

    def test_process_http_error(self):
        from core import HttpError
        with mock.patch('batch.function.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = HttpError(123, 'foo')

            actual = function.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 123)
            self.assertEqual(actual.get_body(), b'{"message": "foo", "request_id": "uuid"}')

    def test_process_internal_server_error(self):
        with mock.patch('batch.function.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = KeyError('foo')

            actual = function.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 500)
            self.assertEqual(actual.get_body(), b'{"message": "Internal Server Error", "request_id": "uuid"}')

    def test_process(self):
        from core import HttpResponse, BatchResponse

        with mock.patch('batch.function.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.return_value = HttpResponse(BatchResponse('foo', []))

            actual = function.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 200)
            self.assertEqual(actual.get_body(), b'{"transfer": "foo", "objects": []}')
