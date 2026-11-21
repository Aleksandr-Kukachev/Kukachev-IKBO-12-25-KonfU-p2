import unittest
from mavengraph.repository import MavenRepository, RepositoryError


class MavenTests(unittest.TestCase):
    def test_bom_import(self):
        bom = (
            b"<project><dependencyManagement><dependencies>"
            b"<dependency><groupId>x</groupId><artifactId>b"
            b"</artifactId><version>9</version></dependency"
            b"></dependencies></dependencyManagement></proj"
            b"ect>"
        )
        child = (
            b"<project><dependencyManagement><dependencies>"
            b"<dependency><groupId>x</groupId><artifactId>b"
            b"om</artifactId><version>1</version><type>pom<"
            b"/type><scope>import</scope></dependency></dep"
            b"endencies></dependencyManagement><dependencie"
            b"s><dependency><groupId>x</groupId><artifactId"
            b">b</artifactId></dependency></dependencies></"
            b"project>"
        )
        repo = MavenRepository(
            "https://example.org", lambda url: bom if "/bom/" in url else child
        )
        self.assertEqual(repo.dependencies("g:a:1"), ["x:b:9"])

    def test_parent_cycle(self):
        xml = (
            b"<project><parent><groupId>g</groupId><artifac"
            b"tId>a</artifactId><version>1</version></paren"
            b"t></project>"
        )
        with self.assertRaisesRegex(RepositoryError, "цикл"):
            MavenRepository("https://example.org", lambda _: xml).dependencies(
                "g:a:1"
            )

    def test_parent_properties_management_and_scopes(self):
        parent = (
            b"<project><properties><lib.version>2</lib.vers"
            b"ion></properties><dependencyManagement><depen"
            b"dencies><dependency><groupId>x</groupId><arti"
            b"factId>b</artifactId><version>${lib.version}<"
            b"/version></dependency></dependencies></depend"
            b"encyManagement></project>"
        )
        child = (
            b"<project"
            b' xmlns="http://maven.apache.org/POM/4.0.0"><p'
            b"arent><groupId>g</groupId><artifactId>p</arti"
            b"factId><version>1</version></parent><dependen"
            b"cies><dependency><groupId>x</groupId><artifac"
            b"tId>b</artifactId></dependency><dependency><g"
            b"roupId>x</groupId><artifactId>test</artifactI"
            b"d><version>1</version><scope>test</scope></de"
            b"pendency></dependencies></project>"
        )
        calls = []

        def fetch(url):
            calls.append(url)
            return parent if "/p/" in url else child

        repo = MavenRepository("https://example.org", fetch)
        self.assertEqual(repo.dependencies("g:a:1"), ["x:b:2"])
        self.assertEqual(
            repo.dependencies("g:a:1", include_all=True), ["x:b:2", "x:test:1"]
        )
        repo.dependencies("g:a:1")
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].endswith("/g/a/1/a-1.pom"))

    def test_invalid_xml(self):
        with self.assertRaises(RepositoryError):
            MavenRepository(
                "https://example.org", lambda _: b"<broken"
            ).dependencies("g:a:1")

    def test_missing_version(self):
        with self.assertRaises(RepositoryError):
            MavenRepository(
                "https://example.org",
                lambda _: (
                    b"<project><dependencies><dependency><groupId>g"
                    b"</groupId><artifactId>b</artifactId></depende"
                    b"ncy></dependencies></project>"
                ),
            ).dependencies("g:a:1")
