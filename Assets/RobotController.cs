using UnityEngine;

public class RobotController : MonoBehaviour
{
    public float moveSpeed = 2f; // Velocidad de movimiento del robot

    private Vector3 targetPosition;
    private bool isMoving;

    // Método para actualizar la posición objetivo
    public void MoveTo(Vector3 newPosition)
    {
        targetPosition = newPosition;
        isMoving = true;
    }

    // Actualiza la posición del robot en cada frame
    void Update()
    {
        if (isMoving)
        {
            // Mueve el robot hacia la posición objetivo
            float step = moveSpeed * Time.deltaTime;
            transform.position = Vector3.MoveTowards(transform.position, targetPosition, step);

            // Detén el movimiento si se alcanza la posición objetivo
            if (Vector3.Distance(transform.position, targetPosition) < 0.001f)
            {
                transform.position = targetPosition; // Asegúrate de que esté exactamente en la posición
                isMoving = false;
            }
        }
    }
}