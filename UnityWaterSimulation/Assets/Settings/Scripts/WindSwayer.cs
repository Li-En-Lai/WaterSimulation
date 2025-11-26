using UnityEngine;

public class WindSwayer : MonoBehaviour
{
    public float wiggleSpeed = 2.0f; // Speed
    public float wiggleIntensity = 0.5f; // Strenght

    private Vector3 originalRotation;

    void Start()
    {
        originalRotation = transform.eulerAngles;
    }

    void Update()
    {
        // Accroding sin count angle
        float zOffset = Mathf.Sin(Time.time * wiggleSpeed) * wiggleIntensity;

        // Count new angle
        Vector3 newRotation = originalRotation + new Vector3(0, 0, zOffset);

        // Rotate Object
        transform.eulerAngles = newRotation;
    }
}