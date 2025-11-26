using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

public class RippleEffect : MonoBehaviour
{
    public int TextureSize = 1024; //Render的Texture大小
    public RenderTexture ObjectsRT; //用於產生Ripple效果的Render Texture
    private RenderTexture CurrRT, PrevRT, TempRT; // CurrRT:儲存當前Frame的水面高度 / PrevRT:儲存上個Frame的水面高度 /TempRT: 臨時Render使用的，用於Texture交換
    public Shader RippleShader, AddShader; // 兩個用於產生Ripple效果的Shader
    private Material RippleMat, AddMat; //基於兩個Shader創建的材質
    // Start is called before the first frame update
    void Start()
    {
        //Creating render textures and materials
        /*Render Texture初始化*/
        
        CurrRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);
        PrevRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);
        TempRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);

        //設置較佳的過濾模式

        CurrRT.filterMode = FilterMode.Bilinear; 
        PrevRT.filterMode = FilterMode.Bilinear;
        TempRT.filterMode = FilterMode.Bilinear;

        CurrRT.anisoLevel = 4;
        PrevRT.anisoLevel = 4;
        TempRT.anisoLevel = 4;

        /*基於兩個產生Ripple效果的Shader創建材質*/
        RippleMat = new Material(RippleShader);
        AddMat = new Material(AddShader);

        //Change the texture in the material of this object to the render texture calculated by the ripple shader.
        //設置Render目標
        //將當前物體的材質中的 _RippleTex 紋理設為 CurrRT
        //物體顯示波紋效果
        GetComponent<Renderer>().material.SetTexture("_RippleTex", CurrRT);

        StartCoroutine(ripples());
    }

    // Update is called once per frame
    IEnumerator ripples()
    {
        //Copy the result of blending the render textures to TempRT.
        //疊加Texture
        AddMat.SetTexture("_ObjectsRT", ObjectsRT);
        AddMat.SetTexture("_CurrentRT", CurrRT);
        Graphics.Blit(null, TempRT, AddMat); //使用Graphics.Blit 將ObjectsRT、CurrRT進行疊加，疊加結果儲存於TempRT

        //Texture交換
        //使疊加後的結果成為當前紋理(CurrRT)
        RenderTexture rt0 = TempRT;
        TempRT = CurrRT;
        CurrRT = rt0;

        //Calculate the ripple animation using ripple shader.
        //設置 前一Frame和當前Frame RippleMat 材質的紋理
        RippleMat.SetTexture("_PrevRT", PrevRT);
        RippleMat.SetTexture("_CurrentRT", CurrRT);
        //使用 RippleShader 計算下一Frame的波紋，結果存儲在 TempRT 中
        Graphics.Blit(null, TempRT, RippleMat);
        //將 TempRT 的內容複製到 PrevRT，為下一次計算做準備
        Graphics.Blit(TempRT, PrevRT);

        //Swap PrevRT and CurrentRT to calculate the result for the next frame.
        //Texture交換
        RenderTexture rt = PrevRT;
        PrevRT = CurrRT;
        CurrRT = rt;

        //Wait for one frame and then execute again.
        yield return null;
        StartCoroutine(ripples());
    }
}
