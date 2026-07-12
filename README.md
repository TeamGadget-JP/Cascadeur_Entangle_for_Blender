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

These four technologies form the foundation shared by every TeamGadget synchronization project, including CEU, CEB, and future tools.<br>
Powered by TeamGadget Core Architecture<br>

# English <br>
# Cascadeur Entangle for Blender (CEB) Beta Test<br>
CEB is the successor to the previous version, **"Gadget Entangle for Cascadeur / Blender (GECB)"**.<br>
While inheriting the core functionality of GECB, CEB has been significantly refined and improved.<br>
With four new technologies, CEB completely removes the CC-dependent workflow of GECB and achieves<br>
**Rig-Agnostic Synchronization** that is independent of any specific rig.<br>

# Development Environment / System Requirements<br>
Windows only (uses Windows API internally)<br>
Blender 5.1.1<br>
Cascadeur Pro 2026.1.3<br>

# CEB Overview<br>
1. Real-time synchronization<br>
2. Rig-Agnostic Synchronization<br>
3. Object Mode / Pose Mode synchronization and synchronization during animation playback<br>
4. Simultaneous synchronization of multiple characters (up to 5 characters)<br>
5. First implementation of the new **Smart Swizzle** technology<br>
6. Improved robustness by assigning a dedicated local port to each character<br>
8. Supports motions with root bone movement<br>
9. Built-in timeline synchronization<br>
10. Individual offline baking support<br>
11. Designed to leave the original rig completely untouched. (Once synchronization is stopped, only the original model remains.)<br>

# What is Rig-Agnostic Synchronization? (Verification Stage)<br>
By dynamically handshaking the bone hierarchy and bone names from Blender to Cascadeur,<br>
the goal is to eliminate retargeting work as much as possible. In theory, any character that can be imported into Blender and Cascadeur and successfully rigged should be able to synchronize.<br>
Whether it is a humanoid, quadruped, mechanical character, multi-legged creature, monster, or any other character that can be rigged in Cascadeur,<br>
it is expected that almost all of them can be synchronized.<br>

Verified Rigs<br>
CC Rig<br>
Mixamo Rig (use **Spine2**)<br>
Dracorex (included with Cascadeur)<br>
Almost all humanoid characters included with Cascadeur<br>

# Local Port Assignment <br>
8920 Reserved for the system<br>
8921 Character 1<br>
8922 Character 2<br>
・<br>
・<br>
8929 Reserved for timeline synchronization<br>

# Installation <br>
1. Place `CEB_Sender_v1.pyc` into the Cascadeur Python plugin folder.<br>
   `[Cascadeur Installation Folder]\resources\scripts\python\commands\`<br>
2. Install `CEB_Receiver_v1.py` as a Blender add-on.<br>

# Usage <br>

Step 1: Import the same character into both Blender and Cascadeur.<br>

Step 2: After Auto-Rigging the character in Cascadeur, return it to its default pose.<br>

&nbsp;&nbsp;&nbsp;&nbsp;**Important:** This is the reference for everything. Always use either an **A-pose** or **T-pose**.<br>

Step 3: In the CEB panel in Blender, assign the target Armature to **Slot0 → Armature**.<br>

Step 4: Enter the bone names for **Root** and **Pelvis1**.<br>

&nbsp;&nbsp;&nbsp;&nbsp;Example:<br>

&nbsp;&nbsp;&nbsp;&nbsp;Mixamo Rig → Root: `mixamorig:Hips` Pelvis1: `mixamorig:Hips`<br>

&nbsp;&nbsp;&nbsp;&nbsp;CC Rig → Root: `CC_Base_BoneRoot` Pelvis1: `CC_Base_Hip`<br>

Step 5: Click **START Entangle** to begin synchronization. Smart Swizzle will also be cached automatically.<br>

&nbsp;&nbsp;&nbsp;&nbsp;If **SS Cached** appears and the button turns blue, everything is ready.<br>

That's all.<br>

# If Synchronization Does Not Work <br>
1. Do both characters have the same bone hierarchy and bone names?<br>
2. Try pressing **START → Stop → START** once on the Blender side.<br>
3. To maintain smooth real-time synchronization, the maximum number of synchronized bones per character is **255** (bone IDs **0–254**).<br>
4. Always start synchronization from Cascadeur first, then Blender.<br>

# Setting Up Multiple Characters in Cascadeur<br>
Example: Setting up two characters<br>
1. Create a scene, then import and rig the first character as usual.<br>
2. Create another scene for the second character. Import and rig the second character as usual.<br>
3. Save and close the scene containing the second character.<br>
4. Return to the first character's scene, then select `File -> Import -> Import Scene To Current...` and import the second scene.<br>
5. The second character's bone names will automatically receive the `character1:` prefix.<br>
6. The third character can be added in the same way.<br>

# Timeline Synchronization and Offline Baking<br>
1. Use the **Sync TimeLine** button to enable/disable timeline synchronization, and use the **Blender / Cascadeur** button to switch the master.<br>
2. In **Bake Targets**, select the slot containing the character(s) you want to bake.<br>
3. Set Blender as the master, specify the bake range, then click **Bake Selected Targets** to start baking.<br>
4. The default **Bake Delay** value is recommended. Adjust it if necessary to match your PC environment.<br>

# About Offline Baking<br>
Animations baked offline can be used as they are.<br>
Once your character animation is complete and synchronization is no longer needed,<br>
simply remove the character from its slot.<br>
The baked animation will then become standard animation data in Blender,<br>
just like animation created directly within Blender.<br>

# After Finalizing the Animation...<br>
Once a character's animation has been finalized, simply remove it from its slot and it will return to its original state.<br>
I say "return," but in reality, nothing was ever modified on the original rig.<br>
The character is only being controlled temporarily during synchronization.<br>
This is what I consider the most elegant part of the Gadget tools—we never modify the original rig.<br>
Once synchronization is finished, every trace disappears without a trace.<br>
That's the TeamGadget philosophy—something I believe cannot easily be replicated elsewhere.<br>

Team Gadget YouTube<br>
https://www.youtube.com/channel/UCj9OYwzMAIgYAeVkTV4wczw<br>

# Disclaimer <br>
CEB is an independent project developed by TeamGadget.<br>
Cascadeur is a trademark and/or property of Nekki.<br>
Blender is a trademark and/or property of Blender Foundation.<br>
This project is not an official product of Nekki or Blender Foundation, and is not endorsed by, affiliated with, sponsored by, or officially supported by either organization.<br>

---

# 日本語 <br>
# Cascadeur Entangle for Blender (CEB) βテスト<br>
CEBは前作"Gadget Entangle for Cascadeur / Blender (GECB)"の後継バージョンになります。<br>
基本的な機能全般はGECBを継承しつつ、大幅にブラッシュアップを施しました。<br>
4つの新技術により前作GECBのCC準拠を完全撤廃、リグに依存しないリグ・アグノスティック同期を実現しました。<br>

# 開発・動作環境<br>
Windows専用 (コード内でWindowsAPIを使用)<br>
Blender 5.1.1<br>
CascadeurPro 2026.1.3<br>

# CEBの概要<br>
1. リアルタイム同期<br>
2. リグ・アグノスティック同期<br>
3. Object Mode / Pose Mode同期・アニメーション再生中同期<br>
4. 複数キャラクター同時同期 (最大5体まで)<br>
5. 新機能 Smart Swizzle 初搭載<br>
6. キャラクター個別にローカルポートを割り当てることで堅牢化<br>
8. ルートボーン移動を伴うモーションに対応<br>
9. タイムライン同期を標準搭載<br>
10. 個別オフライン・ベイク機能搭載<br>
11. 素体に一切改変を加えない設計。(同期を切ればそこには元のモデルだけが残ります)<br>

# リグ・アグノスティック同期とは?　（検証段階）<br>
Blenderから動的にボーン階層・名称をCascadeurとハンドシェイクすることにより<br>
リターゲット作業を徹底的に排除することを目標としました。Blender、Cascadeurにインポートして<br>
リギングできるキャラクターなら理論上何でも同期できると考えています。<br>
それが例えば人間型であろうが四足型であろうがメカ、多足、クリーチャー、その他、Cascadeurで<br>
リギングできるキャラクターならほぼ全て同期できると予想しています。<br>

確認済みのリグ<br>
CCリグ<br>
mixamoリグ(Spine2を使用すること)<br>
Cascadeur同梱のDracorex(恐竜リグ)<br>
Cascadeur同梱の人型キャラクターほぼ全て<br>

# ローカルポート割り当て <br>
8920 システム専用<br>
8921 キャラクター1<br>
8922 キャラクター2<br>
・<br>
・<br>
8929 タイムライン同期専用<br>

# 導入手順 <br>
1. `CEB_Sender_v1.pyc`をCascadeurのPythonプラグインフォルダに配置します。<br>
   `[Cascadeurインストール先]\resources\scripts\python\commands\`<br>
2. `CEB_Receiver_v1.py`をBlenderのアドオン登録<br>

# 使用方法 <br>
step1: 同じキャラクターを双方へインポート<br>

step2: Cascadeur側のキャラクターはオートリギング後、初期ポーズにして下さい。<br>
　　　　重要：これが全ての基準です。必ずAポーズもしくはTポーズで行ってください。<br>

step3: Blender側CEBパネルSlot0のArmture:に同期対象のアーマチャをセットする。<br>

step4: Root:とPelvis1:にボーン名を書き入れます。<br>
　　　　例：mixamoリグならRoot:`mixamorig:Hips` Pelvis1:`mixamorig:Hips`<br>
　　　　CCリグならRoot:`CC_Base_BoneRoot` Pelvis1:`CC_Base_Hip`<br>

step5: START Entangleで同期スタート、同時にSmart Swizzleもキャッシュされます。<br>
　　　　`SS Cashed`となりボタンが青色点灯していればOKです。<br>

以上です。<br>

# 同期しない場合 <br>
1. 双方のキャラクターのボーン構造とボーン名称は一緒ですか?<br>
2. 一度、Blender側のSTART -> Stop -> STARTをやってみましょう。<br>
3. 1キャラクターが持つ同期できるボーンの総量は快適な通信速度を維持するために0～254(255本)です。<br>
4. 同期順はCascadeurが最初でBlender側が後です。<br> 

# Cascadeurでの複数キャラクターセットアップ方法<br>
例 : 2体セットアップ<br>
1. シーンを作成、最初の1体目を通常通りインポート -> リギング。<br>
2. 2体目用に更にシーンを作ります。そのまま2体目を通常通りインポート -> リギング。<br>
3. 2体目が居るシーンを保存して閉じます。<br>
4. 1体目が居るシーンに戻って、`File -> Import -> Import Scene To Current...`で2体目のシーンをインポート。<br>
5. 2体目のボーン名に自動でcharacter1:のプレフィックスが付与されます。<br>
6. 3体目も同じ手順となります。<br>

# タイムライン同期とオフラインベイク<br>
1. Sync TimeLineボタンでオン/オフ、Blender/Cascadeurボタンでマスター切り替え。<br>
2. Bake Targets:でベイクしたいキャラクターがいるSlotを指定します。<br>
3. マスターはBlender側に、ベイク範囲を設定してBake Selected Targetsボタンでベイク開始。<br>
4. Bake DelayはデフォルトでOKです。PC環境に合わせて調整してください。<br>

# オフラインベイクについて<br>
オフラインでベイクしたアニメーションはそのまま使うことができます。<br>
キャラクターアニメーションが完成して、もう同期する必要がなくなったら<br>
キャラクターをスロットから外すだけでBlender内で作成したアニメーションと<br>
変わらないデータとなります。<br>

# アニメーション確定後・・<br>
アニメーションを確定したキャラクターはSlotから外すだけで素体に戻ります。<br>
"戻る"と表現しましたが、そもそも素体に何もしていません。<br>
ただ同期中にキャラクターを一時的に操っているだけです。<br>
これがGadgetツールの最も美しいところで、素体を改変したりは一切しません。<br>
同期が終われば跡形も無く痕跡を消す。これが他では真似できないTeamGadget美学です。<br>

Team Gadget Youtube<br>
https://www.youtube.com/channel/UCj9OYwzMAIgYAeVkTV4wczw<br>

# 免責事項 <br>
CEUはTeamGadgetによる独立したプロジェクトです。<br>
CascadeurはNekkiの商標または財産です。 <br> 
BlenderはBlender Foundationの商標または財産です。<br>

本プロジェクトは、NekkiまたはBlender Foundationによる公式製品ではなく、承認、提携、スポンサー提供、または公式サポートを受けたものではありません。<br>
