import unittest
from mavengraph.repository import MavenRepository, RepositoryError


class MavenTests(unittest.TestCase):
    def test_parent_properties_management_and_scopes(self):
        parent = b'<project><properties><lib.version>2</lib.version></properties><dependencyManagement><dependencies><dependency><groupId>x</groupId><artifactId>b</artifactId><version>${lib.version}</version></dependency></dependencies></dependencyManagement></project>'
        child = b'<project xmlns="http://maven.apache.org/POM/4.0.0"><parent><groupId>g</groupId><artifactId>p</artifactId><version>1</version></parent><dependencies><dependency><groupId>x</groupId><artifactId>b</artifactId></dependency><dependency><groupId>x</groupId><artifactId>test</artifactId><version>1</version><scope>test</scope></dependency></dependencies></project>'
        calls = []
        def fetch(url):
            calls.append(url)
            return parent if '/p/' in url else child
        repo = MavenRepository('https://example.org', fetch)
        self.assertEqual(repo.dependencies('g:a:1'), ['x:b:2'])
        repo.dependencies('g:a:1')
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].endswith('/g/a/1/a-1.pom'))

    def test_invalid_xml(self):
        with self.assertRaises(RepositoryError):
            MavenRepository('https://example.org', lambda _: b'<broken').dependencies('g:a:1')

    def test_missing_version(self):
        with self.assertRaises(RepositoryError):
            MavenRepository('https://example.org', lambda _: b'<project><dependencies><dependency><groupId>g</groupId><artifactId>b</artifactId></dependency></dependencies></project>').dependencies('g:a:1')
