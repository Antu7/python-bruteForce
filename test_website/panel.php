<?php
session_start();
if (isset($_SESSION['logged']) && $_SESSION['logged'] == 1) {
    print("<h1> Panel </h1>");
    print("<a href='logout.php'>Logout</a>");
} else {
    header("Location: index.php");
}
?>