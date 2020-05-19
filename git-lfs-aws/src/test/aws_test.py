import json
import unittest
from unittest import mock

import aws
from aws import *


class ProxyRequestTestCase(unittest.TestCase):
    def test_init(self):
        with open('resources/proxy_request.json', 'r') as f:
            proxy_request = json.loads(f.read())

            actual = ProxyRequest(proxy_request)

            self.assertEqual(actual.resource, '/{proxy+}')
            self.assertEqual(actual.path, '/hello/world')
            self.assertEqual(actual.http_method, 'POST')
            self.assertEqual(actual.headers['Accept'], '*/*')
            self.assertEqual(actual.multi_value_headers['Accept-Encoding'], ['gzip, deflate', ])
            self.assertEqual(actual.query_string_parameters['name'], 'me')
            self.assertEqual(actual.multi_value_query_string_parameters['multivalueName'], ['you', 'me'])
            self.assertEqual(actual.path_parameters['proxy'], 'hello/world')
            self.assertEqual(actual.stage_variables['stageVariableName'], 'stageVariableValue')
            self.assertEqual(actual.request_context['accountId'], '12345678912')
            self.assertEqual(actual.body, '{\r\n\t"a": 1\r\n}')
            self.assertEqual(actual.is_base64_encoded, False)


class ProxyResponseTestCase(unittest.TestCase):
    def test_as_dict(self):
        with open('resources/proxy_response.json', 'r') as f:
            expected = json.loads(f.read())
            response = ProxyResponse(
                is_base64_encoded=True,
                status_code=200,
                headers={"Cache-Control": "max-age=60"},
                multi_value_headers={"multiValueName": ["you", "me"]},
                body={"message": "Hello World!"}
            )

            actual = response.as_dict()

            self.assertEqual(actual, expected)


class S3LargeFileStorageTestCase(unittest.TestCase):

    def setUp(self):
        with mock.patch('boto3.client') as mock_boto_client:
            mock_boto_client.return_value = mock.MagicMock()
            self.lfs = S3LargeFileStorage()
            self.lfs.bucket_name = 'examplebucket'

    def test_exists(self):
        self.lfs.s3.list_objects_v2.return_value = {
            'Name': 'examplebucket',
            'Prefix': 'happyface.jpg',
            'Contents': [
                {
                    'ETag': '"70ee1738b6b21e2c8a43f3a5ab0eee71"',
                    'Key': 'happyface.jpg',
                    'Size': 11,
                    'StorageClass': 'STANDARD',
                }
            ]
        }

        actual = self.lfs.exists('happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertTrue(actual)
        self.lfs.s3.list_objects_v2.assert_called_once_with(
            Bucket='examplebucket',
            Prefix='happyface.jpg',
            MaxKeys=1
        )

    def test_not_exists(self):
        self.lfs.s3.list_objects_v2.return_value = {
            'Name': 'examplebucket',
            'Prefix': 'happyface.jpg'
        }

        actual = self.lfs.exists('happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertFalse(actual)
        self.lfs.s3.list_objects_v2.assert_called_once_with(
            Bucket='examplebucket',
            Prefix='happyface.jpg',
            MaxKeys=1
        )

    def test_presign(self):
        self.lfs.s3.generate_presigned_url.return_value = 'http://examplebucket/happyface.jpg'

        actual = self.lfs.presign('Get/Put object', 'happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertEqual(actual, 'http://examplebucket/happyface.jpg')
        self.lfs.s3.generate_presigned_url.assert_called_once_with(
            'Get/Put object',
            Params={
                'Bucket': 'examplebucket',
                'Key': 'happyface.jpg'
            },
            ExpiresIn=3600
        )

    def test_prepare_download(self):
        self.lfs.presign = mock.MagicMock()
        self.lfs.presign.return_value = 'http://examplebucket/happyface.jpg?action=get_object'

        actual = self.lfs.prepare_download('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'http://examplebucket/happyface.jpg?action=get_object')
        self.lfs.presign.assert_called_once_with('get_object', 'happyface.jpg')

    def test_prepare_upload(self):
        self.lfs.presign = mock.MagicMock()
        self.lfs.presign.return_value = 'http://examplebucket/happyface.jpg?action=put_object'

        actual = self.lfs.prepare_upload('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'http://examplebucket/happyface.jpg?action=put_object')
        self.lfs.presign.assert_called_once_with('put_object', 'happyface.jpg')


class AwsTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_request = mock.MagicMock()
        self.mock_request.path = '/objects/batch'
        self.mock_context = mock.MagicMock()
        self.mock_context.aws_request_id = 'uuid'
        self.mock_facade = mock.MagicMock()
        self.mock_response = mock.MagicMock()

    def test_lambda_handler(self):
        backup_aws_process = aws.process
        aws.process = mock.MagicMock()
        aws.process.return_value = ProxyResponse({"x": "y"})
        with open('resources/proxy_request.json', 'r') as f:
            request = json.loads(f.read())

        actual = aws.lambda_handler(request, 'lambda_context')

        self.assertIsNotNone(actual)
        self.assertEqual(actual['body'], '{"x": "y"}')
        call_args = aws.process.call_args[0]
        self.assertTrue(isinstance(call_args[0], ProxyRequest))
        self.assertEqual(call_args[0].path, '/hello/world')
        self.assertEqual(call_args[1], 'lambda_context')
        aws.process = backup_aws_process

    def test_process_route_not_found(self):
        self.mock_request.path = '/foo'

        actual = aws.process(self.mock_request, self.mock_context)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.status_code, 404)
        self.assertEqual(actual.body, {'message': 'Not found', 'request_id': 'uuid'})

    def test_process_http_error(self):
        from core import HttpError
        with mock.patch('aws.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = HttpError(123, 'foo')

            actual = aws.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 123)
            self.assertEqual(actual.body, {'message': 'foo', 'request_id': 'uuid'})

    def test_process_internal_server_error(self):
        with mock.patch('aws.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = KeyError('foo')

            actual = aws.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 500)
            self.assertEqual(actual.body, {'message': 'Internal Server Error', 'request_id': 'uuid'})

    def test_process(self):
        from core import HttpResponse, BatchResponse

        with mock.patch('aws.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.return_value = HttpResponse(BatchResponse('foo', []))

            actual = aws.process(self.mock_request, self.mock_context)

            self.assertIsNotNone(actual)
            self.assertEqual(actual.status_code, 200)
            self.assertEqual(actual.body, {'objects': [], 'transfer': 'foo'})
