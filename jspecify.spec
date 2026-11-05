Name:		jspecify
Version:	1.0.0
Release:	1
Summary:	Annotations for Java static analysis
Group:		Development/Java
License:	ASL 2.0
URL:		https://jspecify.dev/
Source0:	https://github.com/jspecify/jspecify/archive/refs/tags/v%{version}.tar.gz#/jspecify-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Nullness annotations used by static analysis. jsoup marks its public
types with these. The upstream build is Gradle, so this package compiles
the annotation sources with a flat Maven POM.

%prep
%autosetup -n jspecify-%{version}
# ElementType.MODULE is not in the Java 8 API. Upstream still emits
# class version 52 by compiling with -source 8 -target 8 against the
# running JDK, so --release 8 would hide that constant.
python - <<'PY'
import xml.etree.ElementTree as ET
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

root = ET.Element(tag("project"))
add(root, "modelVersion", "4.0.0")
add(root, "groupId", "org.jspecify")
add(root, "artifactId", "jspecify")
add(root, "version", "%{version}")
add(root, "name", "JSpecify")
props = ET.SubElement(root, tag("properties"))
add(props, "maven.compiler.source", "8")
add(props, "maven.compiler.target", "8")
ET.ElementTree(root).write("pom.xml", encoding="utf-8", xml_declaration=True)
PY

%files -f .mfiles
%doc LICENSE README.md
