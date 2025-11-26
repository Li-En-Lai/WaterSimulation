using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class ChangeScene : MonoBehaviour
{
    public void Update()
    {
       if(Input.GetKeyDown(KeyCode.Space)){
            SceneManager.LoadScene("HandInteractionExamples");
        }
        else if(Input.GetKeyDown(KeyCode.M)){
            SceneManager.LoadScene("MainScene");
        }
        
    }
    
}
