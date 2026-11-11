Name:		jspecify
Version:	1.0.0
Release:	2
Summary:	Annotations for Java static analysis
Group:		Development/Java
License:	ASL 2.0
URL:		https://jspecify.dev/
Provides:	jmod(jspecify)
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
the annotation sources with a flat Maven POM. The jar's automatic module
name is org.jspecify, which JUnit's module-info requires.

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

%build -a
printf 'Automatic-Module-Name: org.jspecify\n' > manifest-extra.mf
jar ufm target/jspecify-%{version}.jar manifest-extra.mf

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
desc=$(jar --describe-module --file target/jspecify-%{version}.jar)
printf '%s\n' "$desc"
if ! printf '%s\n' "$desc" | grep -F -q 'org.jspecify'; then
	exit 1
fi
mkdir -p check
cat > check/Smoke.java << 'EOF'
import java.lang.reflect.AnnotatedType;
import java.lang.reflect.Field;
import org.jspecify.annotations.Nullable;

public class Smoke {
	static @Nullable String name;

	public static void main(String[] args) throws Exception {
		Field field = Smoke.class.getDeclaredField("name");
		AnnotatedType annotated = field.getAnnotatedType();
		Nullable mark = annotated.getAnnotation(Nullable.class);
		if (mark == null) {
			throw new RuntimeException("missing Nullable");
		}
		System.out.println(args[0] + " " + mark.annotationType().getSimpleName());
	}
}
EOF
javac --release 8 -encoding UTF-8 -proc:none -cp target/jspecify-%{version}.jar -d check check/Smoke.java
java -cp "check:target/jspecify-%{version}.jar" Smoke jspecify_ok > check.log
cat check.log
grep -F -q 'jspecify_ok Nullable' check.log

%files -f .mfiles
%doc LICENSE README.md
