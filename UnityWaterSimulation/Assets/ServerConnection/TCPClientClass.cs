using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Net.Sockets;
using System.Threading;

public class TCPClientClass
{
    // 網路連線相關
    private TcpClient client; // 與Server連線的物件(用於建立Client)
    private NetworkStream stream; // 用於與Server進行資料傳輸的管道
    private Thread receiveThread; // 開啟背景Thread，用以持續監聽Server傳遞的資料(避免佔用主Thread)
    private bool isConnected = false; // 紀錄當前Client是否與Server建立連線

    public Action<byte[]> OnImageReceived;

    public bool DebugLog = false;

    public void Connect(string ip, int port)
    {
        try
        {
            // 建立TCP連線
            client = new TcpClient();
            client.Connect(ip, port);
            stream = client.GetStream();
            isConnected = true;

            if (DebugLog)
                Debug.Log($"[已連接到Server] {ip}:{port}");

            // 開始接收資料的執行緒
            receiveThread = new Thread(ReceiveLoop);
            receiveThread.IsBackground = true;
            receiveThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogError($"[連接Server失敗]: {e.Message}");
            isConnected = false;
        }
    }

    public void Disconnect()
    {
        isConnected = false;

        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Join();
            receiveThread = null;
        }

        if (stream != null)
        {
            stream.Close();
        }

        if (client != null)
        {
            client.Close();
        }

        if (DebugLog)
            Debug.Log("結束與Server的連線");
    }

    private void ReceiveLoop()
    {
        while (isConnected)
        {
            try
            {
                // 首先接收圖像大小 (4 bytes)
                byte[] sizeBytes = new byte[4];
                int bytesRead = stream.Read(sizeBytes, 0, 4);
                if (bytesRead != 4) continue;

                int imageSize = (sizeBytes[0] << 24) | (sizeBytes[1] << 16) | (sizeBytes[2] << 8) | sizeBytes[3];
                // 接收圖像資料
                byte[] imageBuffer = new byte[imageSize];
                int totalRead = 0;

                while (totalRead < imageSize)
                {
                    int read = stream.Read(imageBuffer, totalRead, imageSize - totalRead);
                    if (read == 0)
                    {
                        Debug.LogWarning("檢測到Server已關閉");
                        Disconnect();
                        return;
                    }
                    totalRead += read;
                }

                OnImageReceived?.Invoke(imageBuffer);

                if (DebugLog)
                    Debug.Log($"已接收 FlowMap 圖像，大小: {imageSize} 位元組");
            }
            catch (Exception e)
            {
                if (isConnected)
                    Debug.LogError($"接收資料時發生錯誤: {e.Message}");
                Disconnect();
                break;
            }
        }
    }
}
