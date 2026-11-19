Name:		jspecify
Version:	1.0.1
Release:	2
Summary:	Annotations for Java static analysis
Group:		Development/Java
License:	ASL 2.0
URL:		https://jspecify.dev/
Provides:	jmod(jspecify)
Source0:	https://github.com/jspecify/jspecify/archive/refs/tags/v%{version}.tar.gz#/jspecify-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 1.0.0. The tag archive has no prebuilt jars.
Source1:	https://github.com/jspecify/jspecify/archive/refs/tags/v1.0.0.tar.gz#/jspecify-1.0.0.tar.gz
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
name is org.jspecify, which JUnit's module-info requires. 1.0.1 changes
Javadoc only; the annotation semantics are the same. Gradle 9.9.1
strictly pins 1.0.0, so that jar is installed beside 1.0.1.

%prep
%autosetup -n jspecify-%{version}
%setup -q -T -D -a 1 -n jspecify-%{version}
find . -name '*.jar' -delete
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
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
printf 'Automatic-Module-Name: org.jspecify\n' > manifest-extra.mf
jar ufm target/jspecify-%{version}.jar manifest-extra.mf
mkdir -p js100/classes
find jspecify-1.0.0/src/main/java -name '*.java' > js100/sources.list
test "$(wc -l < js100/sources.list)" -eq 5
javac -source 8 -target 8 -encoding UTF-8 -Xlint:-options -d js100/classes @js100/sources.list
printf 'Manifest-Version: 1.0\nAutomatic-Module-Name: org.jspecify\n' > js100/manifest.mf
jar cfm js100/jspecify.jar js100/manifest.mf -C js100/classes .
cat > js100/jspecify.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jspecify</groupId>
  <artifactId>jspecify</artifactId>
  <version>1.0.0</version>
  <name>JSpecify</name>
  <description>Annotations for Java static analysis.</description>
  <url>https://jspecify.dev/</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install -p
sysjar install --buildroot %{buildroot} \
	--artifact js100/jspecify.pom:js100/jspecify.jar \
	--file-name jspecify-1.0.0 \
	--filelist .mfiles100
# 1.0.1 owns jspecify.sysjar. 1.0.0 keeps a second index.
/bin/mv %{buildroot}/usr/share/sysjar/index/org.jspecify/jspecify.sysjar \
	%{buildroot}/usr/share/sysjar/index/org.jspecify/jspecify-1.0.0.sysjar
sed -i 's|/usr/share/sysjar/index/org.jspecify/jspecify\.sysjar|/usr/share/sysjar/index/org.jspecify/jspecify-1.0.0.sysjar|' .mfiles100

%install -a
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles100

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
# Java 8 jar has no --describe-module. The manifest carries the name.
jar xf target/jspecify-%{version}.jar META-INF/MANIFEST.MF
cat META-INF/MANIFEST.MF
grep -F -q 'Automatic-Module-Name: org.jspecify' META-INF/MANIFEST.MF
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
javac -source 8 -target 8 -encoding UTF-8 -Xlint:-options -cp target/jspecify-%{version}.jar -d check check/Smoke.java
java -cp "check:target/jspecify-%{version}.jar" Smoke jspecify_ok > check.log
cat check.log
grep -F -q 'jspecify_ok Nullable' check.log

%check -a
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
javac -source 8 -target 8 -encoding UTF-8 -Xlint:-options \
	-cp %{buildroot}%{_javadir}/jspecify-1.0.0.jar -d check check/Smoke.java
java -cp "check:%{buildroot}%{_javadir}/jspecify-1.0.0.jar" Smoke jspecify100_ok > check100.log
cat check100.log
grep -F -q 'jspecify100_ok Nullable' check100.log

%files -f .mfiles
%doc LICENSE README.md
