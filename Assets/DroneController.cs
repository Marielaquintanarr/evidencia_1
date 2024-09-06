using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class FPSController : MonoBehaviour
{
    public Transform TargetLocation;
    public Camera playerCamera;
    public float walkSpeed = 6f;
    public float lookSpeed = 2f;
    public float lookXLimit = 45f;

    Vector3 moveDirection = Vector3.zero;
    float rotationX = 0;
    public bool canMove = true;

    CharacterController characterController;

    // Queue to store target coordinates
    private Queue<Vector3> targetQueue = new Queue<Vector3>();

    void Start()
    {
        characterController = GetComponent<CharacterController>();
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        // Example coordinates to add to the queue
        targetQueue.Enqueue(new Vector3(2f, transform.position.y, 3f));
        targetQueue.Enqueue(new Vector3(1f, transform.position.y, 5f));
        targetQueue.Enqueue(new Vector3(10f, transform.position.y, 2f));
    }

    void Update()
    {
        #region Handles Movement
        if (canMove)
        {
            float verticalInput = Input.GetAxis("Vertical"); // W = 1, S = -1
            Vector3 forward = playerCamera.transform.forward;
            forward.y = 0; // Ignore vertical movement from the camera's forward direction
            forward.Normalize();
            moveDirection = forward * verticalInput * walkSpeed;
        }

        characterController.Move(moveDirection * Time.deltaTime);
        #endregion

        #region Handles Rotation
        if (canMove)
        {
            rotationX += -Input.GetAxis("Mouse Y") * lookSpeed;
            rotationX = Mathf.Clamp(rotationX, -lookXLimit, lookXLimit);
            playerCamera.transform.localRotation = Quaternion.Euler(rotationX, 0, 0);
            transform.rotation *= Quaternion.Euler(0, Input.GetAxis("Mouse X") * lookSpeed, 0);
        }
        #endregion

        if (Input.GetKeyDown(KeyCode.Space) && targetQueue.Count > 0)
        {
            // Get the next target position from the queue
            Vector3 nextTarget = targetQueue.Dequeue();

            // Add the current transform's x and z to the dequeued target position
            Vector3 targetWithOffset = new Vector3(nextTarget.x + transform.position.x, transform.position.y, nextTarget.z + transform.position.z);

            // Start moving to the new position with the offset
            StartCoroutine(MoveTo(targetWithOffset));
        }
    }

    // Coroutine to move to the specified position
    public IEnumerator MoveTo(Vector3 targetPosition)
    {
        while (Vector3.Distance(transform.position, targetPosition) > 0.1f) // Check if close enough to the target
        {
            Vector3 direction = (targetPosition - transform.position).normalized;
            characterController.Move(direction * walkSpeed * Time.deltaTime);
            yield return null; // Wait for the next frame
        }
    }
}
