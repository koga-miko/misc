車載Android 連絡先プロバイダとアシスタント連携 調査報告書
目次
	1.	エグゼクティブサマリー
	2.	ContactsProviderの概要
	3.	Bluetooth PBAP連携
	4.	Google Assistantとの統合
	5.	ContentObserverによる変更通知
	6.	独自アシスタント実装シーケンス
	7.	実装ガイド
	8.	推奨事項

エグゼクティブサマリー
調査目的
車載AndroidのContactsProviderを活用し、Bluetooth HFP接続された外部端末の連絡先をGoogleアシスタントまたは独自アシスタントから利用する実装方法を調査。
主要な発見事項
	∙	ContactsProviderは2009年（Android 2.0）から存在し、現在も基本設計は変わらず安定
	∙	PBAP連携は2020年頃（AAOS 10-11）から実用化
	∙	Google Assistantは2016年から連絡先連携機能を保有、AAOSでは2020年から本格活用
	∙	ContentObserverによるリアルタイム変更通知が可能
	∙	contents.dbではなくcontacts2.db（ContactsProvider）が標準
推奨アーキテクチャ

[Bluetooth HFP/PBAP] 
    ↓ vCard同期
[ContactsProvider (contacts2.db)]
    ↓ ContentObserver
[独自アシスタント / Google Assistant]
    ↓ 音声認識・発信
[Telecom Framework] → [Bluetooth HFP]


ContactsProviderの概要
1. 歴史的背景
Android 1.0 (2008年) - 初代Contacts API
	∙	シンプルな1テーブル構造
	∙	基本的な連絡先管理のみ
Android 2.0 (Eclair, 2009年10月) - ContactsContract API登場
これが現在のContactsProviderの基礎
主な特徴：
	∙	3層構造の導入（RawContacts → Data → Contacts）
	∙	複数アカウント対応
	∙	ソーシャル統合機能
	∙	リッチなデータ型

// 新API (Android 2.0以降、現在も使用)
Cursor cursor = getContentResolver().query(
    ContactsContract.Contacts.CONTENT_URI,
    null, null, null, null);


その後の主な進化



|バージョン      |年   |主な変更              |
|-----------|----|------------------|
|Android 4.0|2011|UI改善、統合機能強化       |
|Android 5.0|2014|マテリアルデザイン対応       |
|Android 6.0|2015|**ランタイムパーミッション導入**|
|Android 11 |2020|自動統合アルゴリズム改善      |
|Android 14 |2023|部分的アクセス権限検討       |

2. データベース構造
3層アーキテクチャ

┌─────────────────────────────────────┐
│ Contacts                             │  ← 集約レイヤー（表示用）
│ - _ID                                │
│ - DISPLAY_NAME                       │
│ - HAS_PHONE_NUMBER                   │
└─────────────────────────────────────┘
            ↑ 集約
┌─────────────────────────────────────┐
│ RawContacts                          │  ← アカウント単位
│ - _ID                                │
│ - ACCOUNT_TYPE                       │
│ - ACCOUNT_NAME                       │
│ - CONTACT_ID (→ Contacts)           │
└─────────────────────────────────────┘
            ↑ 参照
┌─────────────────────────────────────┐
│ Data                                 │  ← 詳細データ
│ - _ID                                │
│ - RAW_CONTACT_ID (→ RawContacts)    │
│ - MIMETYPE                           │
│ - DATA1, DATA2, ... (電話番号等)    │
└─────────────────────────────────────┘


物理ファイル配置

# ContactsProviderデータベース
/data/data/com.android.providers.contacts/databases/contacts2.db

# 旧版（非推奨）
/data/data/com.android.providers.contacts/databases/contacts.db


3. 基本的な使用方法
連絡先の読み取り

// 権限チェック
if (ContextCompat.checkSelfPermission(context, 
        Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
    // 権限リクエスト
    ActivityCompat.requestPermissions(activity,
        new String[]{Manifest.permission.READ_CONTACTS}, 
        REQUEST_CODE);
}

// ContentResolverを取得
ContentResolver resolver = getContentResolver();

// 連絡先一覧の取得
Cursor cursor = resolver.query(
    ContactsContract.Contacts.CONTENT_URI,
    new String[] {
        ContactsContract.Contacts._ID,
        ContactsContract.Contacts.DISPLAY_NAME,
        ContactsContract.Contacts.HAS_PHONE_NUMBER
    },
    null,  // WHERE句
    null,  // WHERE句の引数
    ContactsContract.Contacts.DISPLAY_NAME + " ASC"  // ソート順
);

if (cursor != null && cursor.moveToFirst()) {
    do {
        String id = cursor.getString(cursor.getColumnIndex(
            ContactsContract.Contacts._ID));
        String name = cursor.getString(cursor.getColumnIndex(
            ContactsContract.Contacts.DISPLAY_NAME));
        int hasPhone = cursor.getInt(cursor.getColumnIndex(
            ContactsContract.Contacts.HAS_PHONE_NUMBER));
        
        // 電話番号がある場合、詳細を取得
        if (hasPhone > 0) {
            Cursor phoneCursor = resolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                new String[] {
                    ContactsContract.CommonDataKinds.Phone.NUMBER,
                    ContactsContract.CommonDataKinds.Phone.TYPE
                },
                ContactsContract.CommonDataKinds.Phone.CONTACT_ID + " = ?",
                new String[] { id },
                null
            );
            
            while (phoneCursor != null && phoneCursor.moveToNext()) {
                String phoneNumber = phoneCursor.getString(
                    phoneCursor.getColumnIndex(
                        ContactsContract.CommonDataKinds.Phone.NUMBER));
                int phoneType = phoneCursor.getInt(
                    phoneCursor.getColumnIndex(
                        ContactsContract.CommonDataKinds.Phone.TYPE));
                
                Log.d("Contact", name + ": " + phoneNumber);
            }
            if (phoneCursor != null) phoneCursor.close();
        }
    } while (cursor.moveToNext());
    cursor.close();
}


連絡先の書き込み（バッチ操作）

// 権限チェック
if (ContextCompat.checkSelfPermission(context, 
        Manifest.permission.WRITE_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
    // 権限リクエスト
}

ContentResolver resolver = getContentResolver();
ArrayList<ContentProviderOperation> ops = new ArrayList<>();

// 1. RawContactの作成
ops.add(ContentProviderOperation.newInsert(
        ContactsContract.RawContacts.CONTENT_URI)
    .withValue(ContactsContract.RawContacts.ACCOUNT_TYPE, "com.bluetooth.hfp")
    .withValue(ContactsContract.RawContacts.ACCOUNT_NAME, "BluetoothDevice_XX:XX:XX")
    .build());

// 2. 名前の追加
ops.add(ContentProviderOperation.newInsert(
        ContactsContract.Data.CONTENT_URI)
    .withValueBackReference(ContactsContract.Data.RAW_CONTACT_ID, 0)
    .withValue(ContactsContract.Data.MIMETYPE,
        ContactsContract.CommonDataKinds.StructuredName.CONTENT_ITEM_TYPE)
    .withValue(ContactsContract.CommonDataKinds.StructuredName.DISPLAY_NAME,
        "山田太郎")
    .build());

// 3. 電話番号の追加
ops.add(ContentProviderOperation.newInsert(
        ContactsContract.Data.CONTENT_URI)
    .withValueBackReference(ContactsContract.Data.RAW_CONTACT_ID, 0)
    .withValue(ContactsContract.Data.MIMETYPE,
        ContactsContract.CommonDataKinds.Phone.CONTENT_ITEM_TYPE)
    .withValue(ContactsContract.CommonDataKinds.Phone.NUMBER, "090-1234-5678")
    .withValue(ContactsContract.CommonDataKinds.Phone.TYPE,
        ContactsContract.CommonDataKinds.Phone.TYPE_MOBILE)
    .build());

// 4. バッチ実行
try {
    ContentProviderResult[] results = resolver.applyBatch(
        ContactsContract.AUTHORITY, ops);
    Log.d("Contact", "連絡先追加成功: " + results.length + "件");
} catch (Exception e) {
    Log.e("Contact", "連絡先追加失敗", e);
}


Bluetooth PBAP連携
1. PBAP (Phone Book Access Profile) の歴史
仕様策定
	∙	Bluetooth SIG策定: 2006年
	∙	Bluetooth 2.0 + EDR時代から存在
AndroidでのPBAPサポート



|バージョン      |年        |機能              |役割              |
|-----------|---------|----------------|----------------|
|Android 2.0|2009     |PBAPサーバー        |スマホ→車載機へ連絡先提供   |
|Android 4.0|2011     |PBAP安定化         |互換性向上           |
|Android 9.0|2018     |**PBAPクライアント追加**|車載機→スマホから連絡先取得  |
|AAOS 10    |2019     |PBAPクライアント強化    |実用レベルの実装        |
|AAOS 11-12 |2020-2021|**実用化**         |Polestar 2等で商用展開|

2. PBAP連携のアーキテクチャ

┌──────────────────────┐
│  外部スマートフォン   │
│  - 連絡先データ       │
└──────────────────────┘
          │
          │ Bluetooth PBAP
          │ (vCard形式)
          ↓
┌──────────────────────┐
│  車載AAOS            │
│  PBAPクライアント     │
│  - vCardパーサー     │
└──────────────────────┘
          │
          │ ContentResolver.applyBatch()
          ↓
┌──────────────────────┐
│  ContactsProvider    │
│  contacts2.db        │
│  account_type=       │
│  "com.android.       │
│   bluetooth.         │
│   pbapclient"        │
└──────────────────────┘


3. PBAP同期の典型的なシーケンス

sequenceDiagram
    participant Phone as 外部スマートフォン
    participant BT as Bluetooth HFP/PBAP
    participant PBAP as PBAPクライアント
    participant Parser as vCardパーサー
    participant CP as ContactsProvider
    
    Note over Phone,BT: 1. Bluetooth接続確立
    Phone->>BT: HFP接続完了
    
    Note over BT,PBAP: 2. PBAP接続
    BT->>PBAP: PBAP接続要求
    PBAP->>Phone: OBEX接続
    Phone-->>PBAP: 接続確立
    
    Note over PBAP,Phone: 3. 連絡先取得
    PBAP->>Phone: PullPhoneBook要求
    Phone-->>PBAP: vCardデータ送信
    Note over Phone: BEGIN:VCARD<br/>VERSION:3.0<br/>FN:山田太郎<br/>TEL:090-1234-5678<br/>END:VCARD
    
    Note over PBAP,Parser: 4. vCardパース
    PBAP->>Parser: vCardデータ
    Parser->>Parser: パース処理
    Parser-->>PBAP: Contact構造体
    
    Note over PBAP,CP: 5. ContactsProvider書き込み
    PBAP->>CP: applyBatch()
    Note over CP: RawContacts挿入<br/>Data挿入（名前、電話番号）
    CP->>CP: contacts2.db更新
    CP-->>PBAP: 書き込み成功
    
    Note over CP: 6. 変更通知
    CP->>CP: notifyChange()


4. AOSPでのPBAPクライアント実装

# PBAPクライアントのソースコード位置
packages/apps/Bluetooth/src/com/android/bluetooth/pbapclient/
├── PbapClientService.java        # メインサービス
├── PbapClientStateMachine.java   # 状態管理
├── PbapClientConnectionHandler.java  # OBEX接続管理
├── BluetoothPbapClient.java      # 公開API (@SystemApi)
└── VCardParser.java              # vCard解析


PBAPクライアントの主要クラス

// @SystemApi - システムアプリのみ使用可能
public final class BluetoothPbapClient implements BluetoothProfile {
    
    // 連絡先のプル
    public boolean pullPhoneBook(String path) {
        // OBEX経由で連絡先取得
    }
    
    // 状態取得
    public int getConnectionState(BluetoothDevice device) {
        // 接続状態を返す
    }
}


5. PBAP連携の確認コマンド

# PBAPサービスの状態確認
adb shell dumpsys bluetooth_manager | grep -i pbap

# PBAP経由で同期された連絡先の確認
adb shell content query --uri content://com.android.contacts/raw_contacts \
  --where "account_type='com.android.bluetooth.pbapclient'"

# Bluetooth接続状態の確認
adb shell dumpsys bluetooth_manager | grep -A 10 "Profile:"


Google Assistantとの統合
1. Google Assistantの歴史
Google Now（前身） - 2012年
	∙	Android 4.1 (Jelly Bean) で登場
	∙	「OK Google」で連絡先検索・発信が可能
	∙	ContactsProviderとの基本連携を実装
Google Assistant - 2016年5月
	∙	Google I/O 2016で正式発表
	∙	Google HomeとPixelスマートフォン向け
	∙	最初からContactsProvider連携機能を搭載
	∙	より自然な会話形式の音声認識
2. 車載環境での展開
Android Auto（スマホ投影型）- 2015年

[スマートフォン]
    ├─ ContactsProvider
    ├─ Google Assistant (or 音声検索)
    └─ 画面・音声をHU（ヘッドユニット）へ投影
         ↓ USB/Wireless
    [車載HU]
         └─ Android Autoアプリで表示


	∙	初期バージョンから連絡先を使った音声発信に対応
	∙	スマートフォンのContactsProviderに直接アクセス
Android Auto + Google Assistant - 2017年
	∙	Android AutoにGoogle Assistantが統合
	∙	より自然な会話での連絡先検索
	∙	「〇〇さんに電話して」「〇〇さんにメッセージ送って」
Android Automotive OS (AAOS) - 2017年発表、2020年本格展開

[車載AAOS（組み込みOS）]
    ├─ ContactsProvider（車載側に存在）
    ├─ Google Assistant（ネイティブ統合）
    ├─ Bluetooth PBAP（スマホから連絡先同期）
    └─ Telecom Framework（発信管理）


	∙	Polestar 2 (2020年) で初の商用展開
	∙	車載OS自体にGoogle Assistantが統合
	∙	車載システムのContactsProviderを直接参照
	∙	Bluetooth PBAP経由で同期した連絡先も利用可能
3. Google Assistantの連絡先活用シーケンス

sequenceDiagram
    participant User as ユーザー
    participant Assistant as Google Assistant
    participant SR as 音声認識
    participant CP as ContactsProvider
    participant Telecom as Telecom Framework
    participant BT as Bluetooth HFP
    
    User->>Assistant: "Hey Google, 山田さんに電話して"
    Assistant->>SR: 音声認識開始
    SR->>SR: STT (Speech-to-Text)
    SR-->>Assistant: "山田さんに電話して"
    
    Assistant->>Assistant: インテント解析
    Note over Assistant: Intent: CALL<br/>Entity: "山田"
    
    Assistant->>CP: query(ContactsContract.Contacts)
    Note over Assistant,CP: display_name LIKE '%山田%'
    CP-->>Assistant: 検索結果
    
    alt 複数候補
        Assistant->>User: "山田太郎さん、山田花子さん、どちらですか？"
        User->>Assistant: "山田太郎"
        Assistant->>CP: 絞り込み検索
        CP-->>Assistant: 山田太郎の電話番号
    end
    
    Assistant->>User: "山田太郎さんに発信します"
    Assistant->>Telecom: placeCall(tel:090-xxxx-xxxx)
    Telecom->>BT: HFP発信コマンド
    BT->>BT: AT+ATD=090xxxxxxxx;
    
    Assistant->>User: "発信しました"


4. 技術的実装
Google Assistantが使用するAPI

// VoiceInteractionService（公開API、Android 5.0以降）
public abstract class VoiceInteractionService extends Service {
    
    @Override
    public void onReady() {
        // 音声認識準備完了
    }
    
    // 音声コマンド処理（実装は非公開）
    protected void handleVoiceCommand(String command) {
        // Google独自実装
        // ContactsProviderへのアクセス
        // Telecom Frameworkへの発信要求
    }
}


ContactsProvider連携

// Google Assistantの内部処理（推測）
private void handleCallIntent(String targetName) {
    // 1. 連絡先検索
    ContentResolver resolver = getContentResolver();
    Cursor cursor = resolver.query(
        ContactsContract.Contacts.CONTENT_URI,
        PROJECTION,
        ContactsContract.Contacts.DISPLAY_NAME + " LIKE ?",
        new String[]{"%" + targetName + "%"},
        null
    );
    
    // 2. 曖昧性解消
    if (cursor.getCount() > 1) {
        askForClarification(cursor);
    } else if (cursor.getCount() == 1) {
        String phoneNumber = getPhoneNumber(cursor);
        placeCall(phoneNumber);
    }
}


5. AAOS環境での確認方法

# Google Assistantのパッケージ確認
adb shell pm list packages | grep assistant
# package:com.google.android.apps.googleassistant

# 連絡先へのアクセス権限確認
adb shell dumpsys package com.google.android.apps.googleassistant | grep -A 5 "granted=true"

# ContactsProviderの連絡先数確認
adb shell content query --uri content://com.android.contacts/contacts | wc -l

# 音声認識サービスの確認
adb shell dumpsys voice_interaction


ContentObserverによる変更通知
1. ContentObserverの概要
ContentObserverは、ContentProviderのデータ変更を監視し、変更があった際に通知を受け取る仕組みです。
基本的な動作フロー

[ContentProvider]
    ├─ insert/update/delete実行
    ├─ notifyChange(uri)呼び出し
    └─ 登録済みのObserverに通知
         ↓
[ContentObserver]
    └─ onChange(uri)コールバック実行


2. ContentObserverの実装
基本実装

public class ContactsChangeObserver extends ContentObserver {
    private Context context;
    
    public ContactsChangeObserver(Context context, Handler handler) {
        super(handler);
        this.context = context;
    }
    
    @Override
    public void onChange(boolean selfChange) {
        super.onChange(selfChange);
        Log.d("Contacts", "連絡先が変更されました（詳細不明）");
        // 変更された連絡先を再読み込み
        reloadContacts();
    }
    
    @Override
    public void onChange(boolean selfChange, Uri uri) {
        super.onChange(selfChange, uri);
        Log.d("Contacts", "連絡先が変更されました: " + uri);
        // URIから変更内容を特定して処理
        handleContactChange(uri);
    }
    
    private void reloadContacts() {
        // 連絡先の再読み込み処理
        new Thread(() -> {
            List<Contact> contacts = loadAllContacts();
            // UIスレッドで更新
            Handler mainHandler = new Handler(Looper.getMainLooper());
            mainHandler.post(() -> {
                updateUI(contacts);
            });
        }).start();
    }
    
    private void handleContactChange(Uri uri) {
        // 特定の連絡先の変更処理
        if (uri.toString().contains("contacts")) {
            String contactId = uri.getLastPathSegment();
            Log.d("Contacts", "Contact ID: " + contactId + " が変更されました");
            
            // 変更内容を取得して処理
            Contact updatedContact = loadContact(contactId);
            if (updatedContact != null) {
                onContactUpdated(updatedContact);
            } else {
                onContactDeleted(contactId);
            }
        }
    }
}


Serviceでの監視実装

public class ContactsMonitorService extends Service {
    private ContactsChangeObserver observer;
    private HandlerThread handlerThread;
    
    @Override
    public void onCreate() {
        super.onCreate();
        
        // バックグラウンドスレッドでハンドラを作成
        handlerThread = new HandlerThread("ContactsObserver");
        handlerThread.start();
        Handler handler = new Handler(handlerThread.getLooper());
        
        // Observerの作成
        observer = new ContactsChangeObserver(this, handler);
        
        // 監視開始
        ContentResolver resolver = getContentResolver();
        
        // すべての連絡先変更を監視
        resolver.registerContentObserver(
            ContactsContract.Contacts.CONTENT_URI,
            true,  // 子URIの変更も監視（重要！）
            observer
        );
        
        Log.d("Contacts", "連絡先の監視を開始しました");
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        // 監視停止
        getContentResolver().unregisterContentObserver(observer);
        handlerThread.quit();
        Log.d("Contacts", "連絡先の監視を停止しました");
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}


3. 詳細な監視（複数URIを監視）

public class DetailedContactsMonitor {
    private Context context;
    private List<ContentObserver> observers = new ArrayList<>();
    private Handler handler;
    
    public void startMonitoring(Context context) {
        this.context = context;
        HandlerThread thread = new HandlerThread("ContactsMonitor");
        thread.start();
        handler = new Handler(thread.getLooper());
        
        ContentResolver resolver = context.getContentResolver();
        
        // 1. Contacts全体の変更監視
        ContentObserver contactsObserver = new ContentObserver(handler) {
            @Override
            public void onChange(boolean selfChange, Uri uri) {
                Log.d("Monitor", "Contacts変更: " + uri);
                onContactsChanged(uri);
            }
        };
        resolver.registerContentObserver(
            ContactsContract.Contacts.CONTENT_URI, 
            true, 
            contactsObserver
        );
        observers.add(contactsObserver);
        
        // 2. RawContacts（アカウント別連絡先）の変更監視
        ContentObserver rawContactsObserver = new ContentObserver(handler) {
            @Override
            public void onChange(boolean selfChange, Uri uri) {
                Log.d("Monitor", "RawContacts変更: " + uri);
                onRawContactsChanged(uri);
            }
        };
        resolver.registerContentObserver(
            ContactsContract.RawContacts.CONTENT_URI, 
            true, 
            rawContactsObserver
        );
        observers.add(rawContactsObserver);
        
        // 3. Data（電話番号など詳細データ）の変更監視
        ContentObserver dataObserver = new ContentObserver(handler) {
            @Override
            public void onChange(boolean selfChange, Uri uri) {
                Log.d("Monitor", "Data変更: " + uri);
                onDataChanged(uri);
            }
        };
        resolver.registerContentObserver(
            ContactsContract.Data.CONTENT_URI, 
            true, 
            dataObserver
        );
        observers.add(dataObserver);
        
        // 4. 電話番号の変更のみを監視
        ContentObserver phoneObserver = new ContentObserver(handler) {
            @Override
            public void onChange(boolean selfChange, Uri uri) {
                Log.d("Monitor", "Phone変更: " + uri);
                onPhoneChanged(uri);
            }
        };
        resolver.registerContentObserver(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI, 
            true, 
            phoneObserver
        );
        observers.add(phoneObserver);
    }
    
    private void onContactsChanged(Uri uri) {
        // Contacts層での変更処理
        Log.d("Monitor", "連絡先が集約レベルで変更されました");
    }
    
    private void onRawContactsChanged(Uri uri) {
        // RawContacts層での変更処理（PBAP同期時など）
        Log.d("Monitor", "アカウント別連絡先が変更されました");
        
        // PBAP連絡先かチェック
        if (isPbapContact(uri)) {
            Log.d("Monitor", "Bluetooth連絡先の同期を検知");
            onPbapContactsSynced();
        }
    }
    
    private void onDataChanged(Uri uri) {
        // Data層での変更処理
        Log.d("Monitor", "連絡先の詳細データが変更されました");
    }
    
    private void onPhoneChanged(Uri uri) {
        // 電話番号の変更処理
        Log.d("Monitor", "電話番号が変更されました");
    }
    
    private boolean isPbapContact(Uri uri) {
        ContentResolver resolver = context.getContentResolver();
        String contactId = uri.getLastPathSegment();
        
        Cursor cursor = resolver.query(
            ContactsContract.RawContacts.CONTENT_URI,
            new String[] { ContactsContract.RawContacts.ACCOUNT_TYPE },
            ContactsContract.RawContacts._ID + " = ?",
            new String[] { contactId },
            null
        );
        
        if (cursor != null && cursor.moveToFirst()) {
            String accountType = cursor.getString(0);
            cursor.close();
            return "com.android.bluetooth.pbapclient".equals(accountType);
        }
        return false;
    }
    
    private void onPbapContactsSynced() {
        // PBAP同期完了時の処理
        // 例: 音声認識辞書の更新
    }
    
    public void stopMonitoring() {
        ContentResolver resolver = context.getContentResolver();
        for (ContentObserver observer : observers) {
            resolver.unregisterContentObserver(observer);
        }
        observers.clear();
    }
}


4. PBAP同期専用の監視

public class BluetoothContactsSyncMonitor extends ContentObserver {
    private static final String PBAP_ACCOUNT_TYPE = "com.android.bluetooth.pbapclient";
    private Context context;
    private ContactsSyncListener listener;
    
    public interface ContactsSyncListener {
        void onSyncStarted();
        void onSyncProgress(int current, int total);
        void onSyncCompleted(int count);
        void onSyncFailed(Exception e);
    }
    
    public BluetoothContactsSyncMonitor(Context context, Handler handler, 
                                        ContactsSyncListener listener) {
        super(handler);
        this.context = context;
        this.listener = listener;
    }
    
    @Override
    public void onChange(boolean selfChange, Uri uri) {
        super.onChange(selfChange, uri);
        
        // PBAP経由の連絡先かチェック
        if (isPbapContact(uri)) {
            Log.d("PBAP", "Bluetooth連絡先が更新されました: " + uri);
            
            // 同期状態を確認
            checkSyncStatus();
        }
    }
    
    private boolean isPbapContact(Uri uri) {
        ContentResolver resolver = context.getContentResolver();
        
        Cursor cursor = resolver.query(
            ContactsContract.RawContacts.CONTENT_URI,
            new String[] { ContactsContract.RawContacts.ACCOUNT_TYPE },
            ContactsContract.RawContacts._ID + " = ?",
            new String[] { uri.getLastPathSegment() },
            null
        );
        
        if (cursor != null && cursor.moveToFirst()) {
            String accountType = cursor.getString(0);
            cursor.close();
            return PBAP_ACCOUNT_TYPE.equals(accountType);
        }
        return false;
    }
    
    private void checkSyncStatus() {
        // PBAP連絡先の総数を確認
        ContentResolver resolver = context.getContentResolver();
        
        Cursor cursor = resolver.query(
            ContactsContract.RawContacts.CONTENT_URI,
            new String[] { "COUNT(*)" },
            ContactsContract.RawContacts.ACCOUNT_TYPE + " = ?",
            new String[] { PBAP_ACCOUNT_TYPE },
            null
        );
        
        if (cursor != null && cursor.moveToFirst()) {
            int count = cursor.getInt(0);
            cursor.close();
            
            Log.d("PBAP", "PBAP連絡先数: " + count);
            
            if (listener != null) {
                listener.onSyncCompleted(count);
            }
        }
    }
}


5. パフォーマンス最適化（スロットリング）
頻繁な変更通知によるパフォーマンス低下を防ぐため、スロットリングを実装します。

public class ThrottledContactsObserver extends ContentObserver {
    private static final long THROTTLE_DELAY_MS = 500; // 500ms
    private Handler handler;
    private Runnable pendingUpdate;
    private ContactChangeListener listener;
    
    public interface ContactChangeListener {
        void onContactsChanged();
    }
    
    public ThrottledContactsObserver(Handler handler, ContactChangeListener listener) {
        super(handler);
        this.handler = handler;
        this.listener = listener;
    }
    
    @Override
    public void onChange(boolean selfChange, Uri uri) {
        // 既存の保留中の更新をキャンセル
        if (pendingUpdate != null) {
            handler.removeCallbacks(pendingUpdate);
        }
        
        // 新しい更新を予約（スロットリング）
        pendingUpdate = () -> {
            Log.d("Contacts", "実際の更新処理実行");
            performActualUpdate(uri);
            pendingUpdate = null;
        };
        
        handler.postDelayed(pendingUpdate, THROTTLE_DELAY_MS);
    }
    
    private void performActualUpdate(Uri uri) {
        // 実際の連絡先更新処理
        if (listener != null) {
            listener.onContactsChanged();
        }
    }
}


6. 変更種別の判定

public class ContactChangeDetector {
    private Map<String, ContactSnapshot> contactCache = new ConcurrentHashMap<>();
    
    public void onContactChanged(Uri uri) {
        String contactId = uri.getLastPathSegment();
        ContactSnapshot newSnapshot = loadContactSnapshot(contactId);
        ContactSnapshot oldSnapshot = contactCache.get(contactId);
        
        if (oldSnapshot == null && newSnapshot != null) {
            Log.d("Change", "新規連絡先追加: " + contactId);
            onContactAdded(newSnapshot);
            
        } else if (oldSnapshot != null && newSnapshot == null) {
            Log.d("Change", "連絡先削除: " + contactId);
            onContactDeleted(oldSnapshot);
            
        } else if (oldSnapshot != null && newSnapshot != null) {
            Log.d("Change", "連絡先更新: " + contactId);
            
            // 何が変更されたか詳細判定
            if (!oldSnapshot.name.equals(newSnapshot.name)) {
                Log.d("Change", "名前変更: " + oldSnapshot.name + " → " + newSnapshot.name);
            }
            if (!oldSnapshot.phoneNumbers.equals(newSnapshot.phoneNumbers)) {
                Log.d("Change", "電話番号変更");
            }
            
            onContactUpdated(oldSnapshot, newSnapshot);
        }
        
        // キャッシュ更新
        if (newSnapshot != null) {
            contactCache.put(contactId, newSnapshot);
        } else {
            contactCache.remove(contactId);
        }
    }
    
    private ContactSnapshot loadContactSnapshot(String contactId) {
        // 連絡先データを取得してスナップショット作成
        // null = 削除された
        ContentResolver resolver = // ... get resolver
        
        Cursor cursor = resolver.query(
            ContactsContract.Contacts.CONTENT_URI,
            new String[] {
                ContactsContract.Contacts._ID,
                ContactsContract.Contacts.DISPLAY_NAME
            },
            ContactsContract.Contacts._ID + " = ?",
            new String[] { contactId },
            null
        );
        
        if (cursor == null || !cursor.moveToFirst()) {
            if (cursor != null) cursor.close();
            return null;  // 削除された
        }
        
        ContactSnapshot snapshot = new ContactSnapshot();
        snapshot.id = contactId;
        snapshot.name = cursor.getString(1);
        cursor.close();
        
        // 電話番号取得
        snapshot.phoneNumbers = loadPhoneNumbers(contactId);
        
        return snapshot;
    }
    
    private List<String> loadPhoneNumbers(String contactId) {
        // 電話番号リストを取得
        List<String> numbers = new ArrayList<>();
        // ... implementation
        return numbers;
    }
    
    private void onContactAdded(ContactSnapshot contact) {
        // 追加時の処理
        Log.d("Detector", "新規連絡先: " + contact.name);
    }
    
    private void onContactDeleted(ContactSnapshot contact) {
        // 削除時の処理
        Log.d("Detector", "削除された連絡先: " + contact.name);
    }
    
    private void onContactUpdated(ContactSnapshot oldContact, 
                                   ContactSnapshot newContact) {
        // 更新時の処理
        Log.d("Detector", "更新された連絡先: " + newContact.name);
    }
    
    static class ContactSnapshot {
        String id;
        String name;
        List<String> phoneNumbers;
        // その他必要なフィールド
    }
}


独自アシスタント実装シーケンス
1. システム全体概要

┌─────────────────────────────────────────────────────────────┐
│                    独自アシスタントシステム                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [ユーザー] ──音声──> [マイク]                                │
│                          │                                    │
│                          ↓                                    │
│                   [音声認識エンジン]                           │
│                          │                                    │
│                          ↓                                    │
│                  [自然言語理解 (NLU)]                          │
│                          │                                    │
│                          ↓                                    │
│              [インテントハンドラー]                            │
│                          │                                    │
│          ┌───────────────┼───────────────┐                   │
│          ↓               ↓               ↓                   │
│    [連絡先検索]     [天気情報]     [ナビ起動]                  │
│          │                                                    │
│          ↓                                                    │
│   [ContactsProvider]                                          │
│          │                                                    │
│          ↓                                                    │
│   [Telecom Framework]                                         │
│          │                                                    │
│          ↓                                                    │
│   [Bluetooth HFP] ──> [外部スマートフォン]                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘


2. 初回接続・初期化シーケンス

sequenceDiagram
    participant User as ユーザー
    participant Assistant as 独自アシスタント
    participant BT as Bluetoothサービス
    participant PBAP as PBAPクライアント
    participant CP as ContactsProvider
    participant SR as 音声認識エンジン
    
    User->>BT: スマートフォン接続
    BT->>BT: HFPプロファイル接続
    BT->>PBAP: PBAP接続開始
    PBAP->>BT: vCard取得要求
    BT-->>PBAP: vCard送信（連絡先データ）
    
    PBAP->>CP: ContentResolver.applyBatch()
    Note over PBAP,CP: RawContacts/Data挿入<br/>account_type="com.android.bluetooth.pbapclient"
    CP->>CP: contacts2.db更新
    
    CP->>Assistant: onChange(uri) 通知
    Note over CP,Assistant: ContentObserver経由
    
    Assistant->>CP: query(Contacts.CONTENT_URI)
    CP-->>Assistant: 連絡先リスト返却
    
    Assistant->>Assistant: 連絡先キャッシュ構築
    Note over Assistant: ・名前と電話番号のマッピング<br/>・読み仮名の抽出<br/>・音声認識用辞書作成
    
    Assistant->>SR: カスタム辞書登録
    Note over Assistant,SR: ・"山田太郎" → "やまだたろう"<br/>・"佐藤花子" → "さとうはなこ"
    
    SR-->>Assistant: 辞書登録完了
    Assistant->>User: 連絡先読み込み完了通知


実装コード

public class CustomAssistantService extends Service {
    private ContactsObserver contactsObserver;
    private ContactsCache contactsCache;
    private VoiceRecognitionEngine voiceEngine;
    private HandlerThread observerThread;
    
    @Override
    public void onCreate() {
        super.onCreate();
        
        Log.d("Assistant", "アシスタントサービス起動");
        
        // 連絡先キャッシュ初期化
        contactsCache = new ContactsCache();
        
        // 音声認識エンジン初期化
        voiceEngine = new VoiceRecognitionEngine(this);
        
        // ContentObserver用のバックグラウンドスレッド作成
        observerThread = new HandlerThread("ContactsObserver");
        observerThread.start();
        Handler handler = new Handler(observerThread.getLooper());
        
        // ContentObserver登録
        contactsObserver = new ContactsObserver(handler);
        getContentResolver().registerContentObserver(
            ContactsContract.Contacts.CONTENT_URI,
            true,  // 子URIも監視
            contactsObserver
        );
        
        Log.d("Assistant", "ContentObserver登録完了");
        
        // 初回連絡先読み込み
        new Thread(() -> {
            loadInitialContacts();
        }).start();
    }
    
    private void loadInitialContacts() {
        Log.d("Assistant", "連絡先の初回読み込み開始");
        
        List<Contact> contacts = ContactsLoader.loadAllContacts(this);
        Log.d("Assistant", "読み込んだ連絡先数: " + contacts.size());
        
        // キャッシュ更新
        contactsCache.updateAll(contacts);
        
        // 音声認識辞書更新
        voiceEngine.updateDictionary(contacts);
        
        Log.d("Assistant", "連絡先の初回読み込み完了");
        
        // UI通知（オプション）
        notifyUser("連絡先を" + contacts.size() + "件読み込みました");
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        
        // Observer解除
        getContentResolver().unregisterContentObserver(contactsObserver);
        observerThread.quit();
        
        Log.d("Assistant", "アシスタントサービス停止");
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    // ContentObserver実装
    class ContactsObserver extends ContentObserver {
        public ContactsObserver(Handler handler) {
            super(handler);
        }
        
        @Override
        public void onChange(boolean selfChange, Uri uri) {
            Log.d("Assistant", "連絡先変更検知: " + uri);
            handleContactsChange(uri);
        }
    }
    
    private void notifyUser(String message) {
        // TTS等でユーザーに通知
    }
}


3. データ更新検知シーケンス

sequenceDiagram
    participant User as ユーザー（外部端末）
    participant BT as Bluetoothサービス
    participant PBAP as PBAPクライアント
    participant CP as ContactsProvider
    participant Observer as ContentObserver
    participant Assistant as 独自アシスタント
    participant SR as 音声認識エンジン
    
    User->>User: スマホ側で連絡先編集
    Note over User: 新規追加 or 更新 or 削除
    
    BT->>PBAP: PBAP再同期トリガー
    Note over BT,PBAP: ・定期同期<br/>・手動同期<br/>・接続時再同期
    
    PBAP->>CP: ContentResolver.applyBatch()
    Note over PBAP,CP: 変更内容を反映
    CP->>CP: contacts2.db更新
    
    CP->>Observer: onChange(selfChange=false, uri)
    Note over CP,Observer: content://com.android.contacts/contacts/123
    
    Observer->>Assistant: onContactChanged(uri)
    
    Assistant->>Assistant: 変更種別判定
    Note over Assistant: ・新規追加<br/>・更新<br/>・削除
    
    alt 新規追加の場合
        Assistant->>CP: query(CONTACT_ID)
        CP-->>Assistant: 新規連絡先データ
        Assistant->>Assistant: キャッシュに追加
        Assistant->>SR: 辞書に新規エントリ追加
    else 更新の場合
        Assistant->>CP: query(CONTACT_ID)
        CP-->>Assistant: 更新後連絡先データ
        Assistant->>Assistant: キャッシュ更新
        Assistant->>SR: 辞書エントリ更新
    else 削除の場合
        Assistant->>Assistant: キャッシュから削除
        Assistant->>SR: 辞書エントリ削除
    end
    
    SR-->>Assistant: 辞書更新完了
    Assistant->>User: （必要に応じて）更新通知


実装コード

private void handleContactsChange(Uri uri) {
    String contactId = uri.getLastPathSegment();
    
    Log.d("Assistant", "連絡先ID " + contactId + " の変更を処理");
    
    // 変更種別判定
    Contact newContact = ContactsLoader.loadContact(this, contactId);
    Contact oldContact = contactsCache.get(contactId);
    
    if (oldContact == null && newContact != null) {
        // 新規追加
        Log.d("Assistant", "新規連絡先追加: " + newContact.name);
        onContactAdded(newContact);
        
    } else if (oldContact != null && newContact == null) {
        // 削除
        Log.d("Assistant", "連絡先削除: " + oldContact.name);
        onContactDeleted(oldContact);
        
    } else if (oldContact != null && newContact != null) {
        // 更新
        Log.d("Assistant", "連絡先更新: " + newContact.name);
        onContactUpdated(oldContact, newContact);
    }
}

private void onContactAdded(Contact contact) {
    // キャッシュに追加
    contactsCache.add(contact);
    
    // 音声認識辞書に追加
    voiceEngine.addDictionaryEntry(contact);
    
    Log.d("Assistant", "連絡先追加処理完了: " + contact.name);
}

private void onContactDeleted(Contact contact) {
    // キャッシュから削除
    contactsCache.remove(contact.id);
    
    // 音声認識辞書から削除
    voiceEngine.removeDictionaryEntry(contact);
    
    Log.d("Assistant", "連絡先削除処理完了: " + contact.name);
}

private void onContactUpdated(Contact oldContact, Contact newContact) {
    // キャッシュ更新
    contactsCache.update(newContact);
    
    // 音声認識辞書更新
    voiceEngine.updateDictionaryEntry(oldContact, newContact);
    
    Log.d("Assistant", "連絡先更新処理完了: " + newContact.name);
}


4. 音声発話による電話発信シーケンス

sequenceDiagram
    participant User as ユーザー
    participant Mic as マイク
    participant Assistant as 独自アシスタント
    participant SR as 音声認識エンジン
    participant NLU as 自然言語理解
    participant CP as ContactsProvider
    participant Telecom as Telecomフレームワーク
    participant BT as Bluetoothサービス
    participant Phone as 外部端末
    
    User->>Mic: "ヘイ、アシスタント"
    Mic->>Assistant: ウェイクワード検知
    Assistant->>User: 起動音・LED点灯
    Assistant->>SR: 音声認識開始
    
    User->>Mic: "山田さんに電話して"
    Mic->>SR: 音声データストリーム
    
    SR->>SR: 音声認識処理
    Note over SR: カスタム辞書参照<br/>"やまださん" → "山田"
    SR-->>Assistant: "山田さんに電話して"（テキスト）
    
    Assistant->>NLU: インテント解析
    NLU->>NLU: パターンマッチング
    Note over NLU: Intent: CALL<br/>Target: "山田"
    NLU-->>Assistant: {intent: "call", name: "山田"}
    
    Assistant->>CP: query(Contacts.CONTENT_URI)
    Note over Assistant,CP: WHERE display_name LIKE '%山田%'
    CP-->>Assistant: 検索結果（複数の可能性）
    
    alt 1件のみヒット
        Assistant->>CP: query(Phone.CONTENT_URI)
        Note over Assistant,CP: WHERE contact_id = 123
        CP-->>Assistant: 電話番号: "090-1234-5678"
        
        Assistant->>User: "山田太郎さんに発信します"
        Assistant->>Telecom: startCall(Uri.parse("tel:090-1234-5678"))
        
    else 複数件ヒット
        Assistant->>User: "山田さんが複数います。山田太郎さん、山田花子さん、どちらですか？"
        User->>Mic: "山田太郎"
        Mic->>SR: 音声認識
        SR-->>Assistant: "山田太郎"
        
        Assistant->>CP: query（絞り込み）
        CP-->>Assistant: 山田太郎の電話番号
        Assistant->>User: "山田太郎さんに発信します"
        Assistant->>Telecom: startCall()
        
    else ヒットなし
        Assistant->>User: "山田さんが連絡先に見つかりません"
        Assistant->>Assistant: シーケンス終了
    end
    
    Telecom->>Telecom: ConnectionService取得
    Telecom->>BT: HFP発信コマンド
    Note over Telecom,BT: AT+ATD=09012345678;
    
    BT->>Phone: HFPプロトコル経由発信
    Phone->>Phone: 発信処理
    Phone-->>BT: 呼び出し中
    BT-->>Telecom: STATE_DIALING
    Telecom-->>Assistant: onCallStateChanged(DIALING)
    
    Assistant->>User: "発信中です"
    
    Phone-->>BT: 通話確立
    BT-->>Telecom: STATE_ACTIVE
    Telecom-->>Assistant: onCallStateChanged(ACTIVE)
    
    Assistant->>User: "通話を開始しました"
    Note over Assistant: 通話中UI表示


実装コード

public class CallIntentHandler {
    private Context context;
    private ContactsCache contactsCache;
    private TextToSpeech tts;
    
    public CallIntentHandler(Context context, ContactsCache cache) {
        this.context = context;
        this.contactsCache = cache;
        
        // TTS初期化
        tts = new TextToSpeech(context, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(Locale.JAPAN);
            }
        });
    }
    
    /**
     * 音声認識結果から電話発信を処理
     * @param recognizedText 認識されたテキスト（例: "山田さんに電話して"）
     */
    public void handleCallIntent(String recognizedText) {
        Log.d("CallIntent", "音声コマンド: " + recognizedText);
        
        // "山田さんに電話して" → "山田" 抽出
        String targetName = extractNameFromIntent(recognizedText);
        
        if (targetName == null) {
            speakResponse("電話をかける相手が分かりませんでした");
            return;
        }
        
        Log.d("CallIntent", "発信先: " + targetName);
        
        // 連絡先検索
        List<Contact> matches = searchContacts(targetName);
        
        if (matches.isEmpty()) {
            speakResponse(targetName + "さんが連絡先に見つかりません");
            return;
        }
        
        if (matches.size() == 1) {
            // 1件のみ → 即座に発信
            makeCall(matches.get(0));
            
        } else {
            // 複数件 → 確認
            askForClarification(matches, targetName);
        }
    }
    
    /**
     * 認識テキストから名前を抽出
     */
    private String extractNameFromIntent(String text) {
        // パターンマッチング
        // "〇〇さんに電話して"
        // "〇〇に電話"
        // "〇〇にかけて"
        
        Pattern pattern = Pattern.compile("(.+?)(?:さん)?(?:に|へ)(?:電話|でんわ|tel)");
        Matcher matcher = pattern.matcher(text);
        
        if (matcher.find()) {
            return matcher.group(1).trim();
        }
        
        return null;
    }
    
    /**
     * 連絡先検索
     */
    private List<Contact> searchContacts(String name) {
        ContentResolver resolver = context.getContentResolver();
        
        Cursor cursor = resolver.query(
            ContactsContract.Contacts.CONTENT_URI,
            new String[] {
                ContactsContract.Contacts._ID,
                ContactsContract.Contacts.DISPLAY_NAME,
                ContactsContract.Contacts.HAS_PHONE_NUMBER
            },
            ContactsContract.Contacts.DISPLAY_NAME + " LIKE ?",
            new String[] { "%" + name + "%" },
            null
        );
        
        List<Contact> results = new ArrayList<>();
        if (cursor != null) {
            while (cursor.moveToNext()) {
                String id = cursor.getString(0);
                String displayName = cursor.getString(1);
                int hasPhone = cursor.getInt(2);
                
                if (hasPhone > 0) {
                    String phoneNumber = getPhoneNumber(id);
                    
                    if (phoneNumber != null) {
                        results.add(new Contact(id, displayName, phoneNumber));
                    }
                }
            }
            cursor.close();
        }
        
        Log.d("CallIntent", "検索結果: " + results.size() + "件");
        return results;
    }
    
    /**
     * 連絡先IDから電話番号を取得
     */
    private String getPhoneNumber(String contactId) {
        ContentResolver resolver = context.getContentResolver();
        
        Cursor phoneCursor = resolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            new String[] { 
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.TYPE
            },
            ContactsContract.CommonDataKinds.Phone.CONTACT_ID + " = ?",
            new String[] { contactId },
            ContactsContract.CommonDataKinds.Phone.IS_PRIMARY + " DESC"  // 主番号優先
        );
        
        String phoneNumber = null;
        if (phoneCursor != null && phoneCursor.moveToFirst()) {
            phoneNumber = phoneCursor.getString(0);
            phoneCursor.close();
        }
        
        return phoneNumber;
    }
    
    /**
     * 電話発信
     */
    private void makeCall(Contact contact) {
        Log.d("CallIntent", "発信: " + contact.name + " (" + contact.phoneNumber + ")");
        
        speakResponse(contact.name + "さんに発信します");
        
        // Telecomフレームワーク経由で発信
        Intent intent = new Intent(Intent.ACTION_CALL);
        intent.setData(Uri.parse("tel:" + contact.phoneNumber));
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        
        try {
            context.startActivity(intent);
            
            // 発信状態を監視（オプション）
            monitorCallState();
            
        } catch (SecurityException e) {
            Log.e("CallIntent", "発信権限がありません", e);
            speakResponse("発信できませんでした。権限を確認してください。");
        }
    }
    
    /**
     * 複数候補がある場合の確認
     */
    private void askForClarification(List<Contact> matches, String originalName) {
        StringBuilder message = new StringBuilder();
        message.append(originalName).append("さんが複数います。");
        
        for (int i = 0; i < Math.min(matches.size(), 3); i++) {
            message.append(matches.get(i).name).append("さん、");
        }
        message.append("どちらですか？");
        
        speakResponse(message.toString());
        
        // 次の音声入力を待つ
        // （音声認識エンジンに候補リストを渡して絞り込み）
    }
    
    /**
     * 音声応答
     */
    private void speakResponse(String text) {
        Log.d("CallIntent", "応答: " + text);
        
        if (tts != null) {
            tts.speak(text, TextToSpeech.QUEUE_ADD, null, null);
        }
    }
    
    /**
     * 通話状態の監視（オプション）
     */
    private void monitorCallState() {
        TelecomManager telecomManager = 
            (TelecomManager) context.getSystemService(Context.TELECOM_SERVICE);
        
        // 通話状態の監視実装
        // CallStateListenerを登録して状態変化を追跡
    }
}


5. エラーハンドリングシーケンス

sequenceDiagram
    participant User as ユーザー
    participant Assistant as 独自アシスタント
    participant CP as ContactsProvider
    participant Telecom as Telecomフレームワーク
    participant BT as Bluetoothサービス
    
    User->>Assistant: "田中さんに電話して"
    
    Assistant->>CP: query(連絡先検索)
    
    alt ContactsProviderアクセス失敗
        CP-->>Assistant: SecurityException
        Assistant->>User: "連絡先にアクセスできません。権限を確認してください。"
        
    else 連絡先が見つからない
        CP-->>Assistant: 結果0件
        Assistant->>User: "田中さんが連絡先に見つかりません。"
        Assistant->>User: "連絡先を確認しますか？"
        
    else 電話番号が登録されていない
        CP-->>Assistant: 連絡先あり、電話番号なし
        Assistant->>User: "田中さんの電話番号が登録されていません。"
        
    else Bluetooth未接続
        Assistant->>Telecom: startCall()
        Telecom->>BT: HFP発信要求
        BT-->>Telecom: Bluetooth未接続エラー
        Telecom-->>Assistant: CallException
        Assistant->>User: "スマートフォンが接続されていません。"
        
    else 発信失敗
        Telecom->>BT: 発信コマンド
        BT-->>Telecom: 発信失敗
        Telecom-->>Assistant: STATE_DISCONNECTED
        Assistant->>User: "発信できませんでした。もう一度お試しください。"
    end


6. 連絡先キャッシュの実装

public class ContactsCache {
    // ID → Contact のマップ
    private Map<String, Contact> contactMap = new ConcurrentHashMap<>();
    
    // 名前 → Contact のインデックス（前方一致検索用）
    private Map<String, List<Contact>> nameIndex = new ConcurrentHashMap<>();
    
    // 読み仮名 → Contact のインデックス（音声認識用）
    private Map<String, List<Contact>> phoneticIndex = new ConcurrentHashMap<>();
    
    /**
     * 全連絡先を更新
     */
    public void updateAll(List<Contact> contacts) {
        contactMap.clear();
        nameIndex.clear();
        phoneticIndex.clear();
        
        for (Contact contact : contacts) {
            add(contact);
        }
        
        Log.d("Cache", "キャッシュ更新完了: " + contactMap.size() + "件");
    }
    
    /**
     * 連絡先を追加
     */
    public void add(Contact contact) {
        contactMap.put(contact.id, contact);
        updateIndex(contact);
    }
    
    /**
     * 連絡先を更新
     */
    public void update(Contact contact) {
        Contact old = contactMap.get(contact.id);
        if (old != null) {
            removeFromIndex(old);
        }
        contactMap.put(contact.id, contact);
        updateIndex(contact);
    }
    
    /**
     * 連絡先を削除
     */
    public void remove(String contactId) {
        Contact contact = contactMap.remove(contactId);
        if (contact != null) {
            removeFromIndex(contact);
        }
    }
    
    /**
     * IDで取得
     */
    public Contact get(String contactId) {
        return contactMap.get(contactId);
    }
    
    /**
     * 名前で検索
     */
    public List<Contact> searchByName(String name) {
        String key = normalizeForIndex(name);
        return nameIndex.getOrDefault(key, Collections.emptyList());
    }
    
    /**
     * 読み仮名で検索
     */
    public List<Contact> searchByPhonetic(String phonetic) {
        String key = normalizeForIndex(phonetic);
        return phoneticIndex.getOrDefault(key, Collections.emptyList());
    }
    
    /**
     * 全連絡先を取得
     */
    public List<Contact> getAll() {
        return new ArrayList<>(contactMap.values());
    }
    
    /**
     * インデックス更新
     */
    private void updateIndex(Contact contact) {
        // 名前インデックス更新
        String nameKey = normalizeForIndex(contact.name);
        nameIndex.computeIfAbsent(nameKey, k -> new ArrayList<>()).add(contact);
        
        // 姓だけでも検索できるように
        String[] nameParts = contact.name.split("\\s+");
        if (nameParts.length > 1) {
            String lastName = normalizeForIndex(nameParts[0]);
            nameIndex.computeIfAbsent(lastName, k -> new ArrayList<>()).add(contact);
        }
        
        // 読み仮名インデックス更新
        if (contact.phoneticName != null) {
            String phoneticKey = normalizeForIndex(contact.phoneticName);
            phoneticIndex.computeIfAbsent(phoneticKey, k -> new ArrayList<>())
                .add(contact);
        }
    }
    
    /**
     * インデックスから削除
     */
    private void removeFromIndex(Contact contact) {
        // 名前インデックスから削除
        String nameKey = normalizeForIndex(contact.name);
        List<Contact> nameList = nameIndex.get(nameKey);
        if (nameList != null) {
            nameList.remove(contact);
            if (nameList.isEmpty()) {
                nameIndex.remove(nameKey);
            }
        }
        
        // 読み仮名インデックスから削除
        if (contact.phoneticName != null) {
            String phoneticKey = normalizeForIndex(contact.phoneticName);
            List<Contact> phoneticList = phoneticIndex.get(phoneticKey);
            if (phoneticList != null) {
                phoneticList.remove(contact);
                if (phoneticList.isEmpty()) {
                    phoneticIndex.remove(phoneticKey);
                }
            }
        }
    }
    
    /**
     * 検索用に正規化
     */
    private String normalizeForIndex(String text) {
        if (text == null) return "";
        
        // 小文字化
        text = text.toLowerCase();
        
        // カタカナをひらがなに変換（オプション）
        text = convertKatakanaToHiragana(text);
        
        // 空白を除去
        text = text.replaceAll("\\s+", "");
        
        return text;
    }
    
    private String convertKatakanaToHiragana(String str) {
        StringBuilder sb = new StringBuilder();
        for (char c : str.toCharArray()) {
            if (c >= 0x30A1 && c <= 0x30F6) {
                // カタカナ → ひらがな変換
                sb.append((char) (c - 0x60));
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }
}


実装ガイド
1. 必要な権限

<!-- AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.assistant">
    
    <!-- 連絡先アクセス -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.WRITE_CONTACTS" />
    
    <!-- 電話発信 -->
    <uses-permission android:name="android.permission.CALL_PHONE" />
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />
    
    <!-- Bluetooth -->
    <uses-permission android:name="android.permission.BLUETOOTH" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
    
    <!-- 音声認識 -->
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    
    <!-- フォアグラウンドサービス（AAOS） -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    
    <application>
        <!-- アシスタントサービス -->
        <service
            android:name=".CustomAssistantService"
            android:enabled="true"
            android:exported="false" />
    </application>
</manifest>


2. プロジェクト構成

com.example.assistant/
├── service/
│   └── CustomAssistantService.java      # メインサービス
├── contacts/
│   ├── ContactsLoader.java              # 連絡先読み込み
│   ├── ContactsCache.java               # 連絡先キャッシュ
│   ├── ContactsObserver.java            # 変更監視
│   └── Contact.java                     # 連絡先データクラス
├── voice/
│   ├── VoiceRecognitionEngine.java      # 音声認識
│   ├── WakeWordDetector.java            # ウェイクワード検知
│   └── TextToSpeechManager.java         # 音声合成
├── intent/
│   ├── IntentParser.java                # インテント解析
│   ├── CallIntentHandler.java           # 電話発信処理
│   └── IntentHandler.java               # ハンドラー基底クラス
└── utils/
    ├── PermissionManager.java           # 権限管理
    └── Logger.java                      # ログ出力


3. 開発環境の確認

# AAOS環境の確認
adb shell getprop ro.build.version.release  # Androidバージョン
adb shell getprop ro.product.model          # デバイスモデル

# ContactsProviderの存在確認
adb shell pm list providers | grep contacts

# Bluetoothサービスの確認
adb shell dumpsys bluetooth_manager

# PBAPクライアントの確認
adb shell dumpsys bluetooth_manager | grep -i pbap


4. デバッグ方法

# 連絡先の内容確認
adb shell content query --uri content://com.android.contacts/contacts

# PBAP連絡先のみ確認
adb shell content query --uri content://com.android.contacts/raw_contacts \
  --where "account_type='com.android.bluetooth.pbapclient'"

# ログの確認
adb logcat -s Assistant:D ContactsProvider:D

# 電話発信のテスト（実機必要）
adb shell am start -a android.intent.action.CALL -d tel:0123456789


5. パフォーマンス考慮事項
メモリ使用量
	∙	連絡先が1000件の場合、キャッシュサイズは約2-3MB
	∙	インデックス構造により、さらに2-3MB程度
処理時間
	∙	初回読み込み: 1000件で約500ms-1秒
	∙	ContentObserver通知: 即座（1ms以下）
	∙	音声認識辞書更新: 1000件で約200-500ms
最適化のポイント
	1.	バックグラウンドスレッドで処理
	2.	スロットリングで頻繁な更新を抑制
	3.	必要な情報のみキャッシュ
	4.	インデックスを活用した高速検索

推奨事項
1. アーキテクチャ
推奨構成

[Bluetooth HFP/PBAP] 
    ↓ 
[ContactsProvider]
    ↓ ContentObserver
[独自アシスタント]
    ├─ 連絡先キャッシュ
    ├─ 音声認識エンジン
    └─ インテントハンドラー


非推奨
	∙	contents.dbを連絡先ストレージとして使用（標準外）
	∙	ContactsProviderを経由せずに直接DBアクセス（保守性低下）
2. 実装方針
連絡先管理
	∙	✅ ContactsProviderを標準的な方法で使用
	∙	✅ ContentObserverで変更を監視
	∙	✅ キャッシュを活用して高速検索
	∙	❌ contents.dbへの直接アクセスは避ける
PBAP連携
	∙	✅ AAOS 11以降の標準PBAP機能を活用
	∙	✅ account_type=“com.android.bluetooth.pbapclient”で識別
	∙	✅ 同期完了を検知して音声認識辞書を更新
音声認識
	∙	✅ カスタム辞書に連絡先を登録
	∙	✅ 読み仮名情報を活用
	∙	✅ 曖昧性解消の仕組みを実装
3. テスト項目
機能テスト
	∙	初回連絡先読み込み
	∙	PBAP同期による連絡先追加
	∙	連絡先更新の検知
	∙	連絡先削除の検知
	∙	音声認識による発信
	∙	複数候補の曖昧性解消
	∙	エラーハンドリング
非機能テスト
	∙	1000件以上の連絡先での動作
	∙	長時間動作の安定性
	∙	メモリリークの確認
	∙	Bluetooth切断/再接続時の動作
4. トラブルシューティング
連絡先が同期されない

# PBAP接続状態確認
adb shell dumpsys bluetooth_manager | grep -A 20 "PBAP"

# 権限確認
adb shell dumpsys package com.android.bluetooth | grep -A 5 permission


ContentObserverが通知されない
	∙	registerContentObserverの第2引数をtrueに設定
	∙	HandlerがUIスレッドではなくバックグラウンドスレッドに紐づいているか確認
音声認識精度が低い
	∙	連絡先の読み仮名情報を活用
	∙	カスタム辞書に適切に登録されているか確認
	∙	ノイズキャンセリングの設定確認

まとめ
技術的結論
	1.	ContactsProviderは成熟した標準API
	∙	2009年から基本設計が変わらない安定性
	∙	AAOS環境でも問題なく使用可能
	2.	PBAP連携は2020年頃から実用化
	∙	AAOS 10-11で実用レベル
	∙	標準的な実装パターンが確立
	3.	ContentObserverによるリアルタイム監視が可能
	∙	変更通知を受け取り、即座に対応
	∙	音声認識辞書の動的更新に活用
	4.	Google Assistantは2016年から連絡先連携
	∙	AAOSでは2020年から本格活用
	∙	同様のアーキテクチャで独自実装も可能
実装上の要点
	∙	ContactsProvider標準APIを使用（contents.dbは非推奨）
	∙	ContentObserverで変更を監視
	∙	連絡先キャッシュで高速化
	∙	音声認識辞書の動的更新
	∙	エラーハンドリングの徹底
次のステップ
	1.	プロトタイプ実装
	2.	実機での動作検証
	3.	パフォーマンステスト
	4.	ユーザビリティ評価
	5.	本番実装

報告書作成日: 2026年1月26日対象システム: Android Automotive OS 11以降調査範囲: ContactsProvider, PBAP連携, 音声アシスタント実装​​​​​​​​​​​​​​​​
