# CLAUDE.md
## プロジェクトの概要・目的
- 音声認識に関する状態遷移のためのコードを作成したい
## 使用する言語・フレームワーク・ツール
- Rust言語を使用する
- Rustのstatigを使用する
- C言語からこのライブラリを使うためCFFIを使用する

## ビルド・テストのコマンド
## コーディング規約・スタイル
## ディレクトリ構成のルール
## やってほしいこと
- 以下のステートマシン制御のコードを作成してほしい。外部とのやりとりにはJSONを使って、インターフェースは極力コンパイルせずに済むようにしたい。
  - 音声認識状態
    - 以下の状態を持つ
      1. Initializing: 初期化中
      2. WaitLanguageSet: 初期化失敗中のため次の言語設定を待つ状態
      3. Ready: PTTかWuWで音声認識を受け付けられる状態
      4. PreSession: 音声認識開始できるかどうか、もしできるならどのコンテキストで起動するのかを上位に問い合わせて応答を待っている状態
      5. Session: 音声認識のセッション状態。音声認識対話を繰り返し、最終的に機能実行終了するか、エラー終了するか、中断終了するかで、Readyに戻る。
    - 以下のイベントを受ける
      - Ptt
      - WuWDetected
      - LanguageChanged
  
  - 音声認識状態のSession内の状態
    - 以下の状態を持つ
      1. Prepare: JSONから最初のコンテキストのデータを読みだして、ここで認識すべき語彙をもと
      2. Guidance: バージイン設定が無効の場合は、Prepareの次はこれになる。
      3. GuidanceAndListening: バージイン設定が有効の場合は、Prepareの次はこれになり、同時に音声認識を開始する。
      4. Listening: 上記Guidanceのあと、もしくは上記GuidanceAndListeningの期間中に発話検知イベントを受信しなかった場合、この状態に遷移する。
      5. Speaking: 上記GuidanceAndListeningもしくは上記Listeningの間に、発話検知イベントを受信した場合、この状態に遷移する。
      6. ConditionChecking: 認識結果が通知された場合、もしくは発話タイムアウトを受信した場合、この状態に遷移して、現在のコンテキストで想定しているいくつかの状態のうち、どの状態に属するかを決定して、次の遷移先（FollowupGuidance, TaskExecAndContinue, TaskExecAndEnd, ErrorAndEnd)を決定する。
      7. FollowupGuidance: もし対話継続する場合、かつ次のコンテキストへ進む前にガイダンスを鳴らす必要がある場合に、ここで鳴らす。この次は1へ戻る。
      8. TaskExecAndContinue: 音声認識によって最終的に決定した外部へのアクションを実行し、対話を継続する。Prepareへ。
      9. TaskExecAndEnd: 音声認識によって最終的に決定した外部へのアクションを実行して状態終了する（メインステートの機能実行終了契機に相当）
      10. ErrorAndEnd: エラーガイダンスを流して状態終了する（メインステートのエラー終了契機に相当）
      11. Aborting: 上記7(FollowupGuidance)より上の、対話継続ケースで、中断イベントが通知された場合は、この状態に遷移して終了ガイダンスを流して状態終了する（メインステートの中断終了契機に相当）

    - 以下のイベントを受ける
      - Abort
      - SilentAbort
      - ItemSelected(current_context_id)
      - Back(current_context_id)
  
  - 音声認識状態と並行して存在する動的グラマ生成状態
    - 以下の状態を持つ
      1. Idle: グラマ生成が動いていない状態。グラマ生成要求を受けたら、DataGettingへ進む
      2. DataGetting: 動的グラマを作るためのデータをゲット出来たら、音声認識状態（※別途データ共有モジュールで保持されているものを参照）の状態に応じて、PreSession中でもSession中でもなければGeneratingへ、それ以外ならPending中へ遷移する。
      3. Generating: グラマ生成が動作中の状態。この状態中に再度グラマ生成要求を受けたらキューへ蓄えておく。グラマ生成が終わったら、キューの状態に応じてIdleかDataGetingへ遷移する。もしこの状態中に音声認識状態がPreSession中かSession中へ変化したら、生成中断し、要求をキューの先頭へ退避する
      4. Pending: グラマ生成保留中の状態。音声認識状態がPreSession中でもSession中でもなくなったら、DataGettingへ遷移する。

    - 以下のイベントを受ける
      - GenerateDynanicGrammer(Grammer_id)
      - ChangedSessionStatus(status_id)
      - NotifyData(data)

- MarkdownとMermaidを駆使して、状態遷移図とその補足説明も作成してほしい。
