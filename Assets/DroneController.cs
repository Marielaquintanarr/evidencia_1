using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class FPSController : MonoBehaviour
{
    public Transform OriginLocation;
    public Camera playerCamera;
    public float walkSpeed = 6f;
    public float lookSpeed = 2f;
    public float lookXLimit = 45f;
    public bool isMoving = false;

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

    }

    public Vector3 getGridPosition()
    {
        int gridX = Mathf.RoundToInt(OriginLocation.position.x - transform.position.x);
        int gridZ = Mathf.RoundToInt(OriginLocation.position.z - transform.position.z);

        return new Vector3(Math.Abs(gridX), 0, Math.Abs(gridZ));
    }

    private IEnumerator MoveTo(int x, int z)
    {
        Vector3 targetPosition = new Vector3(OriginLocation.position.x - x, transform.position.y, OriginLocation.position.z - z);

        while (Vector3.Distance(transform.position, targetPosition) > .5f)
        {
            transform.position = Vector3.MoveTowards(transform.position, targetPosition, walkSpeed * Time.deltaTime);
            yield return null; // Yield here to wait for the next frame
        }

        transform.position = targetPosition;
    }

    public IEnumerator MoveThroughPositions(List<DronePosition> positions)
    {
        isMoving = true;
        foreach (var pair in positions)
        {
            yield return StartCoroutine(MoveTo(pair.x, pair.z));
        }
        yield return new WaitForSeconds(5f);
        isMoving = false;
    }


}
