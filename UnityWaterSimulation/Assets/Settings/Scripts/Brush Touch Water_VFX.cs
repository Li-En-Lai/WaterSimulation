using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.VFX;

//[RequireComponent(typeof(AudioSource))]
public class BrushTouchWater_VFX : MonoBehaviour
{
    public VisualEffect BrushTouchWater;
    public AudioClip SFX_Glitter;
    AudioSource Glitter;
    
    private void OnTriggerEnter(Collider other)
    {
        Debug.Log("Brush Entered the Pool");
        BrushTouchWater.Play();

        //SFX
        Glitter = GetComponent<AudioSource>();
        Glitter.PlayOneShot(SFX_Glitter, 0.2f);
    }

    private void OnTriggerExit(Collider other)
    {
        Debug.Log("Brush Exited the Pool");
        BrushTouchWater.Stop();
    }
}