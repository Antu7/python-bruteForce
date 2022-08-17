<?php
session_start();
if (isset($_POST['login_field']) && isset($_POST['password_field'])) {
    $login = $_POST['login_field'];
    $password = $_POST['password_field'];
    if ($login == "admin" && $password == "redwings") {
        $_SESSION['logged'] = 1;
        header("Location: panel.php");
    } else {
        $_SESSION['message'] = "Wrong password";
        header("Location: index.php");
    }
} else {
    header("Location: index.php");
}
?>