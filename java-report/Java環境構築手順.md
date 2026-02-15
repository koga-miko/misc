# Java環境構築手順

## 目次
1. [JDKのインストール](#jdkのインストール)
2. [環境変数の設定](#環境変数の設定)
3. [動作確認](#動作確認)
4. [IDEのセットアップ](#ideのセットアップ)
5. [ビルドツールのセットアップ](#ビルドツールのセットアップ)

## JDKのインストール

### 1. JDKのダウンロード

以下のいずれかのJDKディストリビューションを選択してダウンロードします：

#### ~~Oracle JDK~~ （非推奨）
> **警告**: Oracle JDKは商用利用で高額なライセンス料が発生する可能性があります。OpenJDKの利用を強く推奨します。
- ~~URL:~~
- ~~商用利用の場合はライセンス確認が必要~~

#### OpenJDK
- **Adoptium (Eclipse Temurin)** - 推奨
  - URL: https://adoptium.net/
  - LTS版の利用を推奨（Java 21, 17, 11など）
- **Amazon Corretto**
  - URL: https://aws.amazon.com/corretto/
- **Microsoft Build of OpenJDK**
  - URL: https://www.microsoft.com/openjdk

### 2. インストール実行

1. ダウンロードした`.msi`または`.exe`ファイルを実行
2. インストールウィザードに従って進める
3. インストール先のパスを記録（例：`C:\Program Files\Eclipse Adoptium\jdk-21.0.1.12-hotspot`）

## 環境変数の設定

### 1. JAVA_HOMEの設定

1. スタートメニューで「環境変数」を検索
2. 「システム環境変数の編集」を開く
3. 「環境変数」ボタンをクリック
4. 「システム環境変数」セクションで「新規」をクリック
5. 以下の値を設定：
   - 変数名: `JAVA_HOME`
   - 変数値: JDKのインストールパス（例：`C:\Program Files\Eclipse Adoptium\jdk-21.0.1.12-hotspot`）

### 2. PATHへの追加

1. 「システム環境変数」から`Path`を選択して「編集」
2. 「新規」をクリック
3. `%JAVA_HOME%\bin`を追加
4. 「OK」をクリックして全てのダイアログを閉じる

## 動作確認

新しいコマンドプロンプトまたはPowerShellを開いて以下のコマンドを実行：

```bash
# Javaバージョン確認
java -version

# Javaコンパイラバージョン確認
javac -version
```

**期待される出力例：**
```
openjdk version "21.0.1" 2023-10-17 LTS
OpenJDK Runtime Environment Temurin-21.0.1+12 (build 21.0.1+12-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.1+12 (build 21.0.1+12-LTS, mixed mode, sharing)
```

## IDEのセットアップ

### IntelliJ IDEA（推奨）

1. **ダウンロード**
   - URL: https://www.jetbrains.com/idea/download/
   - Community Edition（無料）またはUltimate Edition

2. **インストール**
   - インストーラーを実行
   - デフォルト設定で問題なし

3. **JDK設定**
   - File → Project Structure → Project
   - SDKで先ほどインストールしたJDKを選択

### Eclipse

1. **ダウンロード**
   - URL: https://www.eclipse.org/downloads/
   - Eclipse IDE for Java Developers

2. **インストール**
   - インストーラーを実行
   - "Eclipse IDE for Java Developers"を選択

3. **JDK設定**
   - Window → Preferences → Java → Installed JREs
   - Addボタンでインストール済みJDKを追加

### Visual Studio Code

1. **ダウンロード**
   - URL: https://code.visualstudio.com/

2. **拡張機能のインストール**
   - Extension Pack for Java（Microsoft製）をインストール
   - このパックには以下が含まれます：
     - Language Support for Java
     - Debugger for Java
     - Test Runner for Java
     - Maven for Java
     - Project Manager for Java

## ビルドツールのセットアップ

### Maven

1. **ダウンロード**
   - URL: https://maven.apache.org/download.cgi
   - Binary zip archiveをダウンロード

2. **インストール**
   - ZIPファイルを展開（例：`C:\Program Files\Apache\maven`）

3. **環境変数設定**
   - `MAVEN_HOME`: Mavenのインストールパス
   - `Path`に`%MAVEN_HOME%\bin`を追加

4. **動作確認**
   ```bash
   mvn -version
   ```

### Gradle

1. **ダウンロード**
   - URL: https://gradle.org/releases/
   - Binary-onlyまたはComplete distribution

2. **インストール**
   - ZIPファイルを展開（例：`C:\Program Files\Gradle\gradle-8.5`）

3. **環境変数設定**
   - `GRADLE_HOME`: Gradleのインストールパス
   - `Path`に`%GRADLE_HOME%\bin`を追加

4. **動作確認**
   ```bash
   gradle -version
   ```

**または** Gradle Wrapperを使用（推奨）
- プロジェクトごとに`gradlew.bat`を使用
- システム全体へのインストール不要

## トラブルシューティング

### javacコマンドが見つからない

- JDKではなくJREをインストールしていないか確認
- 環境変数のPATH設定を再確認
- コマンドプロンプトを再起動

### JAVA_HOMEが認識されない

- 環境変数名のスペルミスを確認
- パスにスペースが含まれる場合、引用符は不要
- システム環境変数として設定されているか確認

### 複数バージョンのJavaを管理したい場合

- **jEnv**（Linux/Mac）や**jabba**（クロスプラットフォーム）の利用を検討
- Windowsの場合、JAVA_HOMEを手動で切り替えるバッチファイルを作成

## 参考リンク

- [Oracle Java Documentation](https://docs.oracle.com/en/java/)
- [OpenJDK Documentation](https://openjdk.org/)
- [Maven Getting Started Guide](https://maven.apache.org/guides/getting-started/)
- [Gradle User Manual](https://docs.gradle.org/current/userguide/userguide.html)
