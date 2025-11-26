using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MultiFingerRipple : MonoBehaviour
{   
    [Header("左手關節觸發Ripple效果的Particle")]
    public GameObject Particle_L;
    [Header("右手關節觸發Ripple效果的Particle")]
    public GameObject Particle_R;
    [Header("左手關節(手掌中心、五隻手指末端)")]
    public List<Transform> leftHandJoints = new List<Transform>();
    [Header("左手關節名稱")]
    public List<string> leftHandJointNames = new List<string>();
    [Header("右手關節(手掌中心、五隻手指末端)")]
    public List<Transform> rightHandJoints = new List<Transform>();
    [Header("右手關節名稱")]
    public List<string> rightHandJointNames = new List<string>();
    [Header("水面設定")]
    public Transform waterSurface;
    [Header("顯示訊息間隔(秒)")]
    public float debugInterval = 0.5f;
    private float lastDebugTime = 0f;

    // Start is called before the first frame update
    void Start()
    {
        /*左右手Particle System初始化*/
        Particle_L.SetActive(false);
        Particle_R.SetActive(false);
    }

    // Update is called once per frame
    void Update()
    {
        float waterHeight = waterSurface.position.y; //取得當前水面高度

        /*左手*/
        List<int> leftTouchingIndices = new List<int>();
        bool leftHandInWater = CheckHandInwater(leftHandJoints, waterHeight , leftTouchingIndices);//檢查左手是否有任何關節於水面以下

        /*若左手有關節於水面以下則啟用掛載於左手的Particle*/
        if (leftHandInWater)
        {
            Vector3 lowestJointPosition = FindLowestJointPosition(leftHandJoints);//找尋左手最低的關節點，用於定位左手Particle
            Particle_L.SetActive(true); //啟用左手Particle以觸發Ripple效果
            Particle_L.transform.position = new(lowestJointPosition.x,waterHeight,lowestJointPosition.z); //設至左手的Particle位置
        }
        /*反之，若左手關節沒有關節於水面以下，則不啟用左手的Particle，無Ripple效果*/
        else
        {
            Particle_L.SetActive(false);
        }

        /*右手*/
        List<int> rightTouchingIndices = new List<int>();
        bool rightHandInWater = CheckHandInwater(rightHandJoints, waterHeight ,rightTouchingIndices);//檢查右手是否有任何關節於水面以下

        /*若右手有關節於水面以下則啟用掛載於右手的Particle*/
        if (rightHandInWater)
        {
            Vector3 lowestJointPosition = FindLowestJointPosition(rightHandJoints);//找尋右手最低的關節點，用於定位右手Particle
            Particle_R.SetActive(true); //啟用右手Particle以觸發Ripple效果
            Particle_R.transform.position = new(lowestJointPosition.x, waterHeight, lowestJointPosition.z); //設置左手的Particle位置
        }
        /*反之，若左手關節沒有關節於水面以下，則不啟用左手的Particle，無Ripple效果*/
        else
        {
            Particle_R.SetActive(false);
        }

        /*顯示左右手觸碰到水面的資訊於Console*/
        if (Time.time - lastDebugTime > debugInterval)
        {
            DisplayTouchingJoints(leftTouchingIndices, rightTouchingIndices);
            lastDebugTime = Time.time;
        }
    }

    /*檢查手部是否有任何關節於水面以下*/
    private bool CheckHandInwater(List<Transform> joints , float waterHeight , List<int>touchingIndices)
    {
        if (joints == null || joints.Count == 0) return false;

        bool anyJointInWater = false;

        //針對手部關節點逐一檢查是否低於水面高度
        for (int i = 0; i < joints.Count; i++)
        {
            Transform joint = joints[i];
            if (joint == null) continue;

            // 檢查關節是否在水面以下
            if (joint.position.y < waterHeight)
            {
                touchingIndices.Add(i);
                anyJointInWater = true;
            }
        }

        return anyJointInWater;
    }

    /*找到最低關節點位置，用於定位Particle位置*/
    private Vector3 FindLowestJointPosition(List<Transform>joints)
    {
        if (joints == null || joints.Count == 0)
            return Vector3.zero;

        Transform lowestJoint = joints[0]; //用於儲存找到的最低關節，初始化為列表中的第一個關節
        float lowestY = float.MaxValue; //用於追蹤目前找到的最低 Y 座標值，初始化為浮點數的最大值

        /*逐一檢查關節列表中的所有關節位置，來找出最低位置*/
        foreach (Transform joint in joints) 
        {
            if (joint == null) continue;

            if (joint.position.y < lowestY) //檢查當前關節的 Y 座標是否小於目前記錄的最低值
            {
                //若是更新 lowestY 為新的最低 Y 座標
                //更新 lowestJoint 為當前關節
                lowestY = joint.position.y; 
                lowestJoint = joint;
            }
        }

        return lowestJoint.position; //回傳最低的關節位置
    }

    /*顯示觸水關節資訊到Console*/
    private void DisplayTouchingJoints(List<int> leftTouchingIndices, List<int> rightTouchingIndices)
    {
        string message = "觸水關節資訊：\n";

        if (leftTouchingIndices.Count > 0)
        {
            message += "左手觸水關節：";
            for (int i = 0; i < leftTouchingIndices.Count; i++)
            {
                int index = leftTouchingIndices[i];
                string jointName = (index < leftHandJointNames.Count) ? leftHandJointNames[index] : "關節" + index;
                message += jointName;
                if (i < leftTouchingIndices.Count - 1) message += ", ";
            }
            message += " "; //"\n"
        }
        else
        {
            message += "左手無觸水關節 "; // "\n"
        }

        if (rightTouchingIndices.Count > 0)
        {
            message += "右手觸水關節：";
            for (int i = 0; i < rightTouchingIndices.Count; i++)
            {
                int index = rightTouchingIndices[i];
                string jointName = (index < rightHandJointNames.Count) ? rightHandJointNames[index] : "關節" + index;
                message += jointName;
                if (i < rightTouchingIndices.Count - 1) message += ", ";
            }
        }
        else
        {
            message += "右手無觸水關節";
        }

        Debug.Log(message);
    }
}
