using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.VFX;

public class Butterfly_VFX : MonoBehaviour
{
    public VisualEffect Butterfly;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if(Input.GetKeyDown(KeyCode.B)){ //B=Butterfly
            Butterfly.Play();
        }
        if(Input.GetKeyUp(KeyCode.S)){ //S=Stop
            Butterfly.Stop();
        }
    }
}
