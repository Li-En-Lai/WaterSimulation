using UnityEngine;
using UnityEngine.Playables;

public class WaterWheel : MonoBehaviour
{
 public float rotationSpeed = 50f;

    void Update()
    {
        float rotationAmount = rotationSpeed * Time.deltaTime;
        transform.Rotate(rotationAmount, 0, 0);
    }
}