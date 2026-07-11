# TeamGadget Core Architecture
**A universal real-time synchronization architecture for character animation across multiple DCC applications and game engines.**
The TeamGadget Core Architecture is a lightweight synchronization framework designed for real-time communication between independent animation applications.
Rather than relying on complex rig-specific solutions, TeamGadget focuses on four fundamental technologies that maximize performance, reliability, and interoperability while minimizing setup and runtime overhead.
## Core Technologies
### Handshake Protocol
Automatic initialization and synchronization of character information before streaming begins.
### O(1) Runtime Cache
Constant-time bone lookup for high-performance real-time synchronization.
### Zero Calibration
Automatic normalization of local transforms to establish a common reference space between different applications.
### Smart Swizzle
Automatic correction of coordinate-system differences using rest-pose quaternion analysis, enabling rig-agnostic synchronization without manual axis configuration.

---

These four technologies form the foundation shared by every TeamGadget synchronization project, including CEU, CEB, and future tools.

# 日本語 <br>
# Cascadeur Entangle for Unity (CEU) βテスト<br>
CEUは前作"Gadget Entangle for Cascadeur (GEC)"の後継バージョンになります。<br>
基本的な機能全般はGECを継承しつつ、大幅にブラッシュアップを施しました。<br>

# 開発・動作環境<br>
Windows専用 (コード内でWindowsAPIを使用)<br>
Unity6.5<br>
エディターバージョン : 6000.5.1f1<br>
レンダーパイプライン : URP<br>
CascadeurPro 2026.1.3<br>

# CEUの概要<br>
1. リアルタイム同期<br>
2. リグ・アグノスティック同期<br>
3. エディターモード同期・プレイモード同期<br>
4. 複数キャラクター同時同期<br>
5. UIを撤廃しインスペクター側に集約<br>
6. キャラクター個別にローカルポートを割り当てることで堅牢化<br>
8. ルートボーン移動を伴うモーションに対応<br>
9. 部位Lerpの実装<br>
10. iCloneフェイシャルとのハイブリッドシステム<br>
11. プロップ転送と同期<br>

# リグ・アグノスティック同期とは?　（検証段階）<br>
Unityから動的にボーン階層・名称をCascadeurとハンドシェイクすることにより<br>
リターゲット作業を徹底的に排除することを目標としました。Unity、Cascadeurにインポートして<br>
リギングできるキャラクターなら理論上何でも同期できると考えています。<br>
それが例えば人間型であろうが四足型であろうがメカ、多足、クリーチャー、その他、Cascadeurで<br>
リギングできるキャラクターならほぼ全て同期できると予想しています。<br>

# ローカルポート割り当て <br>
8900 システム専用<br>
8901 キャラクター1<br>
8902 キャラクター2<br>
・<br>
・<br>
8909 プロップ転送・同期1<br>
8910 プロップ転送・同期2<br>
・<br>
・<br>

# 導入手順 <br>
1. `CEU_Sender_v1.pyc`をCascadeurのPythonプラグインフォルダに配置します。<br>
   `[Cascadeurインストール先]\resources\scripts\python\commands\`<br>
2. `CEU_System_v1.cs``CEU_Avatar_v1.cs``CEU_Prop_v1.cs`をUntyのProjectに任意のフォルダーを作り、ドラッグ・アンド・ドロップ<br>

# 使用方法 <br>
step1: 同じキャラクターを双方へインポート<br>
step2: Cascadeur側`Commands -> CEU_Sender_v1`を選択して通信開始。<br>
step3: Unity側、ヒエラルキーに空のゲームオブジェクトを作成して`CEU_System_v1.cs`をアタッチ<br>
step4: Unity側、ヒエラルキー内の同期したいキャラクターに`CEU_Avatar_v1.cs`をアタッチ<br>
step5: `CEU_System_v1.cs`をアタッチしたゲームオブジェクトのインスペクターで`Connect To Cascadeur`トグルをオン<br>
以上です。<br>

# 同期しない場合 <br>
1. Target Port番号は合ってますか？<br>
2. 8901ポートのキャラクターはプリフィックスは付きませんので`Cascadeur Prefix`は何も記入しません<br>
3. 8902ポート以降から`Cascadeur Prefix`に`character1:``character2:`とプリフィックスを記入します<br>
4. `Rig Type`を`Humanoid`や`Generic`に切り替えてみてください<br>
5. 同期順はCascadeurが最初でUnity側が後です<br>
6. 同期するとキャラクターが小刻みに震えます -> Animatorを切って下さい。キャラクターの奪い合いをしています。<br>
7. UnityのキャラクターとCascadeurのキャラクターのボーン階層構造と名称は一致させてください。<br>
8. 1キャラクターが持つ同期できるボーンの総量は快適な通信速度を維持するために0～254(255本)です。<br>

# Cascadeurでの複数キャラクターセットアップ方法<br>
例 : 2体セットアップ<br>
1. シーンを作成、最初の1体目を通常通りインポート -> リギング。<br>
2. 2体目用に更にシーンを作ります。そのまま2体目を通常通りインポート -> リギング。<br>
3. 2体目が居るシーンを保存して閉じます。<br>
4. 1体目が居るシーンに戻って、`File -> Import -> Import Scene To Current...`で2体目のシーンをインポート。<br>
5. 2体目のボーン名に自動でcharacter1:のプレフィックスが付与されます。<br>
6. 3体目も同じ手順となります。<br>

# プロップの転送と同期<br>
1. UnityからCascadeurに送りたいメッシュモデルに`CEU_Prop_v1.cs`をアタッチ。<br>
2. `CEU_Prop_v1.cs`をアタッチしたメッシュモデルをクリックしてインスペクターを開き`Expoet OBJ...`ボタンを押す。<br>
3. Cascadeur側にメッシュモデルが転送され、即座に同期されます。<br>
注意：転送時にUnity側のメッシュモデルのトランスフォームはリセットされます。<br>
この機能はキャラクターに何かを持たせたりといった事を想定したものです。<br>
背景等のメッシュには適さないので、その際は従来の方法でCascadeurにインポートする事をお勧めします。<br>   

# プロップのメッシュがエディターで同期しない場合 (URP環境)<br>
最新のUnity URP（Universal Render Pipeline）環境において、Cascadeurからの接続時にプロップ（小道具）の<br>
Transform数値は更新されるのに、メッシュの見た目がシーンビュー上で追従しない現象が発生する場合があります。<br> 
これはURPの強力な描画キャッシュ機能がエディターモードで干渉しているために起こります。<br>
以下の手順で設定を変更してください。<br>

1. Projectウィンドウから、現在使用しているURPアセットを選択します（例: Assets/Settings/PC_RPAsset など）。<br>
(※場所が不明な場合は、上部メニューの Edit > Project Settings > Graphics を開き、一番上に設定されて<br>
いるファイルを確認してください)<br>
2. Inspectorウィンドウ上部の Rendering 項目を開きます。<br>
GPU Resident Drawer の設定を Instanced Drawing から Disabled に変更します。<br>

# ルートモーション設定<br>
1. Sync Root Motion のトグルチェックをオンにすることでルートボーンの移動と回転の許可を与えます。<br>
2. Root Bone Name にキャラクターのルートボーン名を入力します。<br>
3. Root Rotation Offset ではCascadeurの座標系とUnity側のキャラクターのルートボーンの座標系を合わせる為に使用します。<br>
例：CC由来のキャラクターではデフォルトでX-90されているので、ここにのXに90を入力することで回転を相殺します。<br>
4. Root Swizzle (Advanced)ではルートボーンの移動方向と回転方向を合わせます、ケースによって様々なパターンがあります。<br>
キャラクターに適合する設定値を探ってください。<br>

# 補完設定 (Lerp)<br>
足首から上と下で個別に補完が設定できるようにしました。<br>

# iCloneフェイシャルとのハイブリッド<br>
Enable iClone Hybrid トグルチェックをオンにすることでNeckとHeadの同期を解除します。<br>
iClone側でもHybrid接続することで1体のキャラクターの体部をCascadeur制御、表情をiClone制御にすることができます。<br>

Team Gadget Youtube<br>
https://www.youtube.com/channel/UCj9OYwzMAIgYAeVkTV4wczw<br>

# 免責事項 <br>
CEUはTeamGadgetによる独立したプロジェクトです。<br>
CascadeurはNekkiの商標または財産です。 <br> 
Unityはunity technologies incの商標または財産です。<br>

本プロジェクトは、Nekkiまたはunity technologies incによる公式製品ではなく、承認、提携、スポンサー提供、または公式サポートを受けたものではありません。<br>
