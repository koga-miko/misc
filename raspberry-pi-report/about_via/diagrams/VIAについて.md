# VIAについて

## 目的
このページでは、Android における 音声操作アプリ(Voice Interaction Application。以降はVIAで記載)の考え方、構成、アプリ間連携、ルールを明確にする。

## VIAの考え方
Android では、音声操作アプリ（我々でいうところの音認アプリや音認サービス）に対する作成のお作法・テンプレートのクラスやインターフェースが用意されている。

### VIAのお作法

```mermaid
%%{init: {'theme':'base', 'themeVariables': {
  'noteBkgColor':'#fff3bf',
  'noteTextColor':'#000',
  'noteBorderColor':'#ffd700',
  'altBkgColor':'#e3f2fd',
  'altBorderColor':'#1976d2',
  'loopBkgColor':'#f3e5f5',
  'loopBorderColor':'#7b1fa2',
  'optBkgColor':'#e8f5e9',
  'optBorderColor':'#388e3c'
}}}%%
sequenceDiagram
    participant A as Alice
    participant B as Bob
    
    Note right of A: これはノート
    
    alt 成功の場合
        A->>B: リクエスト送信
    else 失敗の場合
        A->>B: エラー通知
    end
    
    opt オプション処理
        B->>A: 確認応答
    end
    
    loop 3回繰り返し
        A->>B: データ送信
    end
    
    rect rgb(200, 220, 250)
        A->>B: rect内の処理
    end
```