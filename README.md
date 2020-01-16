# scrape_service



## これは何？


[monkeypython-japan](https://monkeypython-japan.github.io/) のスキル展示を目的とした POC レベルの Django プロジェクトです。

ユーザが指定した URL と Xpath、インターバルに従い、Web ページのスクレイピングを行い、その結果をデータベースに保存します。
スクレイピングのインターバルは、毎日あるいは毎時の指定が出来ます。保存された結果は一覧ページで確認でき、CSV 形式のファイルとしてダウンロードが可能です。

## みていただきたい事


Django のプロジェクトとして実装を行っています。
“registration” app は Web インターフェースを使ってユーザのログイン、スクレイピングの指示内容の入力と変更、データベースへの更新を行います。
“scraper” app は定期的にデータベースからスクレイピングの仕様を取り出し、スクレイピングを実行して結果をデータベースに書き込みます。

このサービスは多数のユーザの登録内容を効率的に処理できるよう、スケーラビリティの実現にを主眼において開発を行っています。
scraper app では、スクレイピング実行の前に、タスクの統合を行い、複数のユーザが同一ページを指定している場合でも、一回のページアクセスで複数のユーザのスクレイピングを実行するようにしています。また、Web ページのアクセスは時間がかかるため、ページアクセスからスクレイピングの実行を複数のスレッドで並列化しています。このことにより多くのユーザのスクレイピングタスクを効率的に処理できます。

## アプリケーション概要


### registration

このサービスのユーザーインターフェースとデータベース管理を担当するアプリケーションです。ユーザ登録と認証、スクレイピングの仕様のメンテナンスから結果のダウンロードが主な機能です。Django の MVC モデルに忠実な実装を行っています。

### scraper

Scraping を実際に実行するアプリケーションで、ユーザとのインタラクションは行いません。タイマーで定期的に実行され、データベースからそのインターバルで実行すべきスクレイピングの仕様を取り出し、スクレイピング処理を行い、結果を各ユーザのデータベースに格納します。スクレイピングの実行前に、タスクの統合を行い、ユーザ間で指定が重複する場合でも、一つのページに一度だけのアクセスで処理するようにタスクをスケジュールします。ページごとにまとまられたタスクは Thead Pool を使用して並列化して実行します。タスクの統合には独自に実装した、多分木ツリーデータ構造を使用しています。また、HTMLパーサには、負荷が少ない xlml.html を使用しています。

## ToDo


* 指定されたインターバルでの実行
  * 現在のインターバルスロットに該当するタスクだけ取り出して実行するようにする。
* CSV ダウンロード
  * 結果ページに、ダウンロードリンクを設置する。
* ~~ログインページ~~
  * ~~登録済みユーザの認証ページをの制作。新規ユーザ登録のリンクもここに設置。~~
* ~~ユーザ登録~~
  * ~~新規ユーザの登録ページの制作。~~