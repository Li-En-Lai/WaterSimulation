using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Duckweed_Move : MonoBehaviour
{
    public Transform Centerpoint;
    public float RotationSpeed = 50f;
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (Centerpoint != null)
        {
            transform.RotateAround(Centerpoint.position, Vector3.up, RotationSpeed * Time.deltaTime);
        }
    }
}
