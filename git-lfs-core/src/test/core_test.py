import unittest
from unittest import mock

from core import *


class CoreTestCase(unittest.TestCase):
    def test_dataclass_as_dict(self):
        response = BatchResponse(
            'basic',
            [
                BatchResponse.ObjectLfs(
                    oid='AQ1SW2DE#',
                    size=None,
                    authenticated=None,
                    actions={
                        'download': BatchResponse.ObjectLfs.Action(
                            href='QWERTYUIO',
                            expires_in=123
                        ),
                        'upload': None
                    },
                    error=BatchResponse.ObjectLfs.Error(
                        code=987,
                        message=None
                    )
                ),
                None
            ]
        )

        actual = dataclass_as_dict(response)

        self.assertEqual(
            {
                'transfer': 'basic',
                'objects': [
                    {
                        'oid': 'AQ1SW2DE#',
                        'actions': {
                            'download': {
                                'href': 'QWERTYUIO',
                                'expires_in': 123
                            }
                        },
                        'error': {
                            'code': 987,
                        }
                    },
                    None
                ]
            },
            actual
        )


class BatchFacadeTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_lfs = mock.MagicMock()
        self.batch_facade = BatchFacade(self.mock_lfs)

    def test_not_found(self):
        request = HttpRequest('/foo', "GET")

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Not found'):
            self.batch_facade.process(request)

    def test_not_found_incorrect_path(self):
        request = HttpRequest('/foo', "POST")

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Not found'):
            self.batch_facade.process(request)

    def test_not_found_incorrect_method(self):
        request = HttpRequest('/objects/batch', "PUT")

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Not found'):
            self.batch_facade.process(request)

    def test_not_acceptable(self):
        request = HttpRequest(
            '/objects/batch', "POST",
            headers={
                'Accept': 'application/json'
            }
        )

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Not Acceptable'):
            self.batch_facade.process(request)

    def test_not_acceptable_missing_header(self):
        request = HttpRequest('/objects/batch', "POST")

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Not Acceptable'):
            self.batch_facade.process(request)

    def test_process(self):
        with open('resources/batch_request.json', 'r') as f:
            http_request = HttpRequest(
                '/objects/batch', "POST",
                headers={
                    'Accept': 'application/vnd.git-lfs+json; charset=utf-8'
                },
                body=f.read()
            )
            self.batch_facade.batch_request = mock.MagicMock()
            self.batch_facade.batch_request.return_value = 'foo'

            actual = self.batch_facade.process(http_request)

            self.assertEqual(actual.status_code, 200)
            self.assertEqual(actual.headers['Content-Type'], 'application/vnd.git-lfs+json')
            self.assertEqual(actual.body, 'foo')
            self.batch_facade.batch_request.assert_called_once()
            batch_request = self.batch_facade.batch_request.call_args[0][0]
            self.assertEqual(batch_request.operation, 'download')
            self.assertEqual(batch_request.transfers, ['basic'])
            self.assertEqual(batch_request.ref.name, 'refs/heads/master')
            self.assertEqual(batch_request.objects[0].oid, '12345678')
            self.assertEqual(batch_request.objects[0].size, 123)

    def test_batch_request_unsupported_transfers(self):
        batch_request = BatchRequest('download', [], transfers=['unknown'])

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Unprocessable Entity'):
            self.batch_facade.batch_request(batch_request)

    def test_batch_request_default_transfers(self):
        batch_request = BatchRequest('download', [])

        actual = self.batch_facade.batch_request(batch_request)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.transfer, 'basic')

    def test_batch_request_unsupported_operation(self):
        batch_request = BatchRequest(
            'delete',
            [
                BatchRequest.ObjectLfs(
                    'QaX1WsC2EdC3',
                    123
                )
            ]
        )

        with self.assertRaisesRegex(expected_exception=HttpError, expected_regex='Unprocessable Entity'):
            self.batch_facade.batch_request(batch_request)

    def test_batch_request_download_operation(self):
        self.mock_lfs.exists.return_value = True
        self.mock_lfs.prepare_download.return_value = BatchResponse.ObjectLfs.Action('url')
        batch_request = BatchRequest(
            'download',
            [
                BatchRequest.ObjectLfs(
                    'QaX1WsC2EdC3',
                    123
                )
            ]
        )

        actual = self.batch_facade.batch_request(batch_request)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.transfer, 'basic')
        self.assertEqual(actual.objects[0].oid, 'QaX1WsC2EdC3')
        self.assertEqual(actual.objects[0].size, 123)
        self.assertTrue(actual.objects[0].authenticated)
        self.assertEqual(actual.objects[0].actions['download'].href, 'url')
        self.assertIsNone(actual.objects[0].actions.get('upload'))
        self.assertIsNone(actual.objects[0].error)
        self.mock_lfs.exists.assert_called_once_with('QaX1WsC2EdC3')
        self.mock_lfs.prepare_download.assert_called_once_with('QaX1WsC2EdC3', 123)

    def test_batch_request_upload_operation(self):
        self.mock_lfs.prepare_upload.return_value = BatchResponse.ObjectLfs.Action('url')
        batch_request = BatchRequest(
            'upload',
            [
                BatchRequest.ObjectLfs(
                    'QaX1WsC2EdC3',
                    123
                )
            ]
        )

        actual = self.batch_facade.batch_request(batch_request)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.transfer, 'basic')
        self.assertEqual(actual.objects[0].oid, 'QaX1WsC2EdC3')
        self.assertEqual(actual.objects[0].size, 123)
        self.assertTrue(actual.objects[0].authenticated)
        self.assertEqual(actual.objects[0].actions['upload'].href, 'url')
        self.assertIsNone(actual.objects[0].actions.get('download'))
        self.assertIsNone(actual.objects[0].error)
        self.mock_lfs.prepare_upload.assert_called_once_with('QaX1WsC2EdC3', 123)

    def test_batch_request_download_object_not_exist(self):
        self.mock_lfs.exists.return_value = False
        batch_request = BatchRequest(
            'download',
            [
                BatchRequest.ObjectLfs(
                    'QaX1WsC2EdC3',
                    123
                )
            ]
        )

        actual = self.batch_facade.batch_request(batch_request)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.transfer, 'basic')
        self.assertEqual(actual.objects[0].oid, 'QaX1WsC2EdC3')
        self.assertEqual(actual.objects[0].size, 123)
        self.assertTrue(actual.objects[0].authenticated)
        self.assertIsNone(actual.objects[0].actions)
        self.assertEqual(actual.objects[0].error.code, 404)
        self.assertEqual(actual.objects[0].error.message, 'The object does not exist on the server')

    def test_batch_request(self):
        self.mock_lfs.exists.return_value = True
        self.mock_lfs.prepare_download.return_value = BatchResponse.ObjectLfs.Action('url')
        batch_request = BatchRequest(
            'download',
            [
                BatchRequest.ObjectLfs(
                    'QaX1WsC2EdC3',
                    123
                ),
                BatchRequest.ObjectLfs(
                    'MkP0NjI9BhU8',
                    987
                )
            ]
        )

        actual = self.batch_facade.batch_request(batch_request)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.transfer, 'basic')
        self.assertEqual(len(actual.objects), 2)
