#!/usr/bin/env python3
"""
.pcapngファイルを解析して、アドレスとポートのペアごとのデータサイズを集計するプログラム

必要なライブラリ:
    pip install pyshark

使用方法:
    python analyze_pcapng.py <pcapngファイルパス>
"""

import sys
import pyshark
from collections import defaultdict
from datetime import datetime


def analyze_pcapng(pcapng_file):
    """
    pcapngファイルを解析して、接続ごとのデータサイズを集計

    Args:
        pcapng_file: .pcapngファイルのパス
    """
    print(f"pcapngファイルを読み込み中: {pcapng_file}\n")

    try:
        # pcapngファイルを開く
        cap = pyshark.FileCapture(pcapng_file)

        # 統計情報を保存する辞書
        # キー: (送信元IP, 送信元ポート, 宛先IP, 宛先ポート, プロトコル)
        # 値: {'packets': パケット数, 'bytes': 総バイト数, 'timestamps': [タイムスタンプリスト]}
        stats = defaultdict(lambda: {'packets': 0, 'bytes': 0, 'timestamps': []})

        total_packets = 0

        print("パケット解析中...")

        # 各パケットを解析
        for packet in cap:
            total_packets += 1

            try:
                # IPレイヤーがあるか確認
                if hasattr(packet, 'ip'):
                    src_ip = packet.ip.src
                    dst_ip = packet.ip.dst
                    protocol = None
                    src_port = None
                    dst_port = None

                    # TCPパケットの場合
                    if hasattr(packet, 'tcp'):
                        protocol = 'TCP'
                        src_port = packet.tcp.srcport
                        dst_port = packet.tcp.dstport
                        packet_size = int(packet.length)

                    # UDPパケットの場合
                    elif hasattr(packet, 'udp'):
                        protocol = 'UDP'
                        src_port = packet.udp.srcport
                        dst_port = packet.udp.dstport
                        packet_size = int(packet.length)

                    else:
                        # TCP/UDP以外のIPパケット
                        protocol = packet.ip.proto
                        src_port = '-'
                        dst_port = '-'
                        packet_size = int(packet.length)

                    # キーを作成（双方向の通信を別々に集計）
                    key = (src_ip, src_port, dst_ip, dst_port, protocol)

                    # 統計情報を更新
                    stats[key]['packets'] += 1
                    stats[key]['bytes'] += packet_size

                    # タイムスタンプを記録
                    if hasattr(packet, 'sniff_timestamp'):
                        stats[key]['timestamps'].append(float(packet.sniff_timestamp))

            except AttributeError as e:
                # パケットの属性にアクセスできない場合はスキップ
                continue

        cap.close()

        print(f"解析完了: {total_packets} パケット\n")

        # 結果を表示
        print("=" * 100)
        print(f"{'送信元アドレス':25} {'送信元ポート':12} {'宛先アドレス':25} {'宛先ポート':12} {'プロトコル':8} {'パケット数':10} {'総バイト数':15}")
        print("=" * 100)

        # バイト数でソート（降順）
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['bytes'], reverse=True)

        total_bytes = 0

        for key, value in sorted_stats:
            src_ip, src_port, dst_ip, dst_port, protocol = key
            packets = value['packets']
            bytes_count = value['bytes']
            total_bytes += bytes_count

            print(f"{src_ip:25} {str(src_port):12} {dst_ip:25} {str(dst_port):12} {protocol:8} {packets:10} {bytes_count:15,}")

        print("=" * 100)
        print(f"{'合計':82} {sum(s['packets'] for s in stats.values()):10} {total_bytes:15,}")
        print("=" * 100)

        # 接続ごとの詳細情報を表示（オプション）
        print_detailed_stats(sorted_stats)

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {pcapng_file}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


def print_detailed_stats(sorted_stats):
    """
    接続ごとの詳細統計情報を表示
    """
    print("\n\n" + "=" * 100)
    print("詳細統計情報")
    print("=" * 100)

    for idx, (key, value) in enumerate(sorted_stats[:10], 1):  # 上位10件のみ表示
        src_ip, src_port, dst_ip, dst_port, protocol = key
        packets = value['packets']
        bytes_count = value['bytes']
        timestamps = value['timestamps']

        print(f"\n[{idx}] {src_ip}:{src_port} → {dst_ip}:{dst_port} ({protocol})")
        print(f"    パケット数: {packets:,}")
        print(f"    総バイト数: {bytes_count:,} bytes ({bytes_count/1024:.2f} KB, {bytes_count/1024/1024:.2f} MB)")
        print(f"    平均パケットサイズ: {bytes_count/packets:.2f} bytes")

        if timestamps and len(timestamps) > 1:
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = end_time - start_time

            # タイムスタンプを日付・時刻に変換
            start_datetime = datetime.fromtimestamp(start_time)
            end_datetime = datetime.fromtimestamp(end_time)

            print(f"    通信開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            print(f"    通信終了時刻: {end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

            if duration > 0:
                print(f"    通信時間: {duration:.2f} 秒")
                print(f"    平均レート: {bytes_count/duration:.2f} bytes/sec ({bytes_count/duration/1024:.2f} KB/sec)")
        elif timestamps and len(timestamps) == 1:
            # パケットが1つだけの場合
            single_time = timestamps[0]
            single_datetime = datetime.fromtimestamp(single_time)
            print(f"    通信時刻: {single_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")


def print_usage():
    """使用方法を表示"""
    print("使用方法:")
    print("  python analyze_pcapng.py <pcapngファイルパス>")
    print("\n例:")
    print("  python analyze_pcapng.py capture.pcapng")
    print("\n必要なライブラリ:")
    print("  pip install pyshark")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("エラー: pcapngファイルを指定してください\n")
        print_usage()
        sys.exit(1)

    pcapng_file = sys.argv[1]
    analyze_pcapng(pcapng_file)
