# 艦これアシスタント (KCAA)

**このプロジェクトは凍結しました。フォークはどうぞご自由に。**

艦これアシスタント(KCAA)は、
[艦これ](http://www.dmm.com/netgame/feature/kancolle.html)
をプレイするためのアシスタントツールです。
公式のFlashクライアントではやりづらい、必要な情報の収集やルーチンワークをアシストすることで、提督が資源管理や意思決定に集中できるようになることを目指して作られています。

現在備わっている主な機能は
- 艦隊・艦船の主要なパラメータの一覧表示
- 一部ルーチンワーク(補充、資源計算しながら遠征)のアシスト
- (実験的) リモートからスクリーンショット見ながら簡易操作

直近で追加を予定している機能は
- 柔軟な艦隊・艦船の一覧(フィルタリング、ソート、他のパラメータ表示など)
- 艦隊編成や装備の記憶・一括再現
- 艦隊の行動や資源の記録・チャート表示
- すべてのルーチンワークのアシスト(提督が怠惰な場合)
- UI/UXをもっとましにする

# クイックインストール

## Windows

まず、必要なサードパーティのソフトウェアを次の場所からダウンロード、インストールします。

- Python 2.7: http://www.python.jp/download/
  - 何を選べばいいかわからなければ
    [python-2.7.6.amd64.msi](http://www.python.org/ftp/python/2.7.6/python-2.7.6.amd64.msi)
    を選びます。
- Pillow for Python 2.7: https://pypi.python.org/pypi/Pillow/2.4.0
  - 何を選べばいいかわからなければ
    [Pillow-2.4.0-win-amd64-py2.7.exe](https://pypi.python.org/packages/2.7/P/Pillow/Pillow-2.4.0.win-amd64-py2.7.exe)
    を選びます。
- Java Runtime Environment (JRE): http://www.java.com/ja/download/

それから、
[Chrome](http://www.google.co.jp/intl/ja/chrome/browser/)
がインストールされていることを確認してください。
`tools-windows/config.bat`を書き換えればFirefoxを選ぶこともできます。

終わったら、最新のリリースパッケージ kcaa_release_vX.X.X.zip
(X.X.Xはバージョン)を
[リリース一覧](https://github.com/kcaa/kcaa/releases)
からダウンロードして解凍してください。
中にある `tools-windows/install.bat` を探して実行します。

これでインストールは終わりです!
プレイするには、 `tools-windows/start_game.bat` を実行します。
二つのChromeブラウザが開き、片方には艦これが、もう片方には艦これアシスタントが立ち上がります。


何か詰まったり質問などあれば、 https://twitter.com/kcaadev で何でも聞いてください。
お待ちしています!

## Ubuntu

まずこのリポジトリを `git clone` してください。

    git clone https://github.com/kcaa/kcaa.git

なんのことかわからなければ、最新のリリースパッケージ kcaa_release_vX.X.X.zip
(X.X.Xはバージョン)を
[リリース一覧](https://github.com/kcaa/kcaa/releases)
からダウンロードして解凍してください。

それから、
[Chrome](http://www.google.co.jp/intl/ja/chrome/browser/)
がインストールされていることを確認してください。
`tools/config`を書き換えればFirefoxを選ぶこともできます。

次に `tools/install.sh` を実行してください。
sudoer権限が必要になります。

    cd kcaa_vX.X.X/tools
    ./install.sh

これでインストールは終わりです!
プレイするには、 `tools/start_game.sh` を実行します。
二つのChromeブラウザが開き、片方には艦これが、もう片方には艦これアシスタントが立ち上がります。

    ./start_game.sh

何か詰まったり質問などあれば、 https://twitter.com/kcaadev で何でも聞いてください。
お待ちしています!

## Mac OS

まずこのリポジトリを `git clone` してください。

    git clone https://github.com/kcaa/kcaa.git

なんのことかわからなければ、最新のリリースパッケージ kcaa_release_vX.X.X.zip
(X.X.Xはバージョン)を
[リリース一覧](https://github.com/kcaa/kcaa/releases)
からダウンロードして解凍してください。

それから、
[Chrome](http://www.google.co.jp/intl/ja/chrome/browser/)
がインストールされていることを確認してください。
`tools/config`を書き換えればFirefoxを選ぶこともできます。

サードパーティライブラリのインストールのため、
[MacPorts](https://www.macports.org/install.php)
も必要です。

[Xcode](https://developer.apple.com/jp/xcode/downloads/)
も必要かもしれません。要らないかもしれませんがXcodeの無い環境では動くかどうかテストしていません。
Xcodeを入れない場合でも、
[Java Runtime Environment](https://java.com/ja/download/)
はインストールしておいてください。

すべて終わったら `tools-mac/install.sh` を実行してください。
sudoer権限が必要になります。

    cd kcaa_vX.X.X/tools-mac
    ./install.sh

これでインストールは終わりです!
プレイするには、 `tools-mac/start_game.sh` を実行します。
二つのChromeブラウザが開き、片方には艦これが、もう片方には艦これアシスタントが立ち上がります。

    ./start_game.sh

何か詰まったり質問などあれば、 https://twitter.com/kcaadev で何でも聞いてください。
お待ちしています!

## その他のLinux

サポートの予定はありませんが、必要なパッケージのインストールスクリプトができればできるはずです。
Pull requestあれば大歓迎します!

# 重要なこと

艦これアシスタントはあるがままの状態で配布されます。
開発・頒布元のKCAA Devは、艦これアシスタントの利用によって損害などが生じたとしても、いかなる形の責任も負いません。
利用する場合は自己責任で行う必要があります。
詳しくは下記の Apache License, Version 2.0 を参照してください。

# ライセンス

艦これアシスタントは Apache License, Version 2.0 の下で頒布されます。

    Copyright 2014 KCAA Dev
    https://github.com/kcaa/kcaa
    Apache License, Version 2.0
    http://www.apache.org/licenses/LICENSE-2.0

ここで言う艦これアシスタントとは、このリポジトリあるいはディレクトリに含まれる、binサブディレクトリ以外のすべてのファイルとサブディレクトリを指します。
サードパーティのソフトウェアにはそれぞれのライセンスと規約が適用されます。
詳しくは thirdparty.txt を参照してください。
